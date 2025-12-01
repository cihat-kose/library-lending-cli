#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Oppgave 4 – Python + MySQL Connector (forbedret)

Endringer (UX-forbedringer):
1) Argumentløst kjør: viser nå automatisk alle bøker (standardhandling).
2) register_utlan: verifiserer at LNr finnes før utlån opprettes.
3) lever_bok: gir tydelig beskjed hvis utlånet allerede er levert.

Bruk:
  python oppgave4.py --host 127.0.0.1 --port 3306 --user root --password ***** --database ga_bibliotek
  python oppgave4.py vis-alle
  python oppgave4.py sok --tekst "Ibsen"
  python oppgave4.py registrer-utlan --isbn 9000000000001 --eksnr 1 --lnr 3
  python oppgave4.py lever-bok --utlansnr 5
  python oppgave4.py historikk --lnr 3

Miljøvariabler støttes også: DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
"""

import argparse
import datetime
import os
import sys
from typing import List, Tuple

try:
    import mysql.connector
    from mysql.connector import Error
except ImportError:
    print("Feil: mysql-connector-python er ikke installert. Kjør: pip install mysql-connector-python")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Hjelpefunksjoner for utskrift
# ---------------------------------------------------------------------------
def _print_table(headers: List[str], rows: List[Tuple]):
    """Skriver ut tabell med dynamiske kolonnebredder."""
    widths = [len(h) for h in headers]
    for r in rows:
        for i, v in enumerate(r):
            widths[i] = max(widths[i], len("" if v is None else str(v)))

    def fmt_row(row):
        return " | ".join(str("" if v is None else v).ljust(widths[i]) for i, v in enumerate(row))

    line = "-".join("-" * (w + 2) for w in widths)
    print(fmt_row(headers))
    print(line)
    for r in rows:
        print(fmt_row(r))
    print()


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
def get_db_args():
    """Bygger felles DB-argumenter fra CLI og miljøvariabler."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--host", default=os.getenv("DB_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("DB_PORT", 3306)))
    parser.add_argument("--user", default=os.getenv("DB_USER", "root"))
    parser.add_argument("--password", default=os.getenv("DB_PASSWORD", ".MySQL01,"))
    parser.add_argument("--database", default=os.getenv("DB_NAME", "ga_bibliotek"))
    return parser


def connect_to_database(ns) -> mysql.connector.MySQLConnection:
    """Oppretter og returnerer en databaseforbindelse basert på navneområdet ns."""
    try:
        conn = mysql.connector.connect(
            host=ns.host, port=ns.port, user=ns.user, password=ns.password, database=ns.database
        )
        if not conn.is_connected():
            raise Error("Klarte ikke å koble til databasen.")
        return conn
    except Error as e:
        print(f"DB-feil: {e}")
        sys.exit(2)


# ---------------------------------------------------------------------------
# Operasjoner
# ---------------------------------------------------------------------------
def vis_alle_boker(conn):
    """Lister alle bøker med sentrale felt."""
    sql = """
          SELECT ISBN, Tittel, Forfatter, Forlag, UtgittÅr, AntallSider
          FROM bok
          ORDER BY Tittel ASC \
          """
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    _print_table(["ISBN", "Tittel", "Forfatter", "Forlag", "UtgittÅr", "AntallSider"], rows)
    cur.close()


def sok_bok(conn, tekst: str):
    """Søk i tittel eller forfatter (case-insensitive pga kollasjon)."""
    pattern = f"%{tekst}%"
    sql = """
          SELECT ISBN, Tittel, Forfatter, UtgittÅr
          FROM bok
          WHERE Tittel LIKE %s
             OR Forfatter LIKE %s
          ORDER BY Forfatter, Tittel \
          """
    cur = conn.cursor()
    cur.execute(sql, (pattern, pattern))
    rows = cur.fetchall()
    _print_table(["ISBN", "Tittel", "Forfatter", "UtgittÅr"], rows)
    cur.close()


def _eksisterer_laner(conn, lnr: int) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM låner WHERE LNr = %s", (lnr,))
    ok = cur.fetchone() is not None
    cur.close()
    return ok


def registrer_utlan(conn, lnr: int, isbn: str, eksnr: int, utlansdato: str | None = None):
    """
    Oppretter et nytt utlån dersom:
      - Låner finnes
      - Eksemplaret finnes
      - Eksemplaret er ikke allerede utlånt (Levert=0)
    """
    try:
        cur = conn.cursor()

        # 1) Sjekk at låner finnes
        if not _eksisterer_laner(conn, lnr):
            print(f"Kan ikke opprette utlån: LNr={lnr} finnes ikke.")
            cur.close()
            return

        # 2) Sjekk at eksemplaret finnes
        cur.execute(
            "SELECT 1 FROM eksemplar WHERE ISBN = %s AND EksNr = %s",
            (isbn, eksnr),
        )
        if cur.fetchone() is None:
            print(f"Kan ikke opprette utlån: Eksemplar finnes ikke (ISBN={isbn}, EksNr={eksnr}).")
            cur.close()
            return

        # 3) Sjekk om eksemplaret allerede er utlånt (Levert=0)
        cur.execute(
            """
            SELECT u.UtlånsNr
            FROM utlån u
            WHERE u.ISBN = %s
              AND u.EksNr = %s
              AND u.Levert = 0
            """,
            (isbn, eksnr),
        )
        if cur.fetchone() is not None:
            print("Kan ikke opprette utlån: Eksemplaret er allerede utlånt (Levert=0).")
            cur.close()
            return

        # 4) Opprett utlån
        #   - Hvis utlansdato er oppgitt, bruk den (YYYY-MM-DD valideres)
        #   - Ellers bruk dagens dato via CURDATE()
        if utlansdato:
            # enkel validering av formatet
            try:
                datetime.date.fromisoformat(utlansdato)
            except Exception:
                print("Ugyldig datoformat for --utlansdato. Bruk YYYY-MM-DD.")
                cur.close()
                return
            cur.execute(
                """
                INSERT INTO utlån (ISBN, EksNr, LNr, Utlånsdato, Levert)
                VALUES (%s, %s, %s, %s, 0)
                """,
                (isbn, eksnr, lnr, utlansdato),
            )
        else:
            cur.execute(
                """
                INSERT INTO utlån (ISBN, EksNr, LNr, Utlånsdato, Levert)
                VALUES (%s, %s, %s, CURDATE(), 0)
                """,
                (isbn, eksnr, lnr),
            )
        conn.commit()
        print("Utlån opprettet.")
        cur.close()
    except Error as e:
        conn.rollback()
        print(f"Feil under registrering av utlån: {e}")


def lever_bok(conn, utlansnr: int):
    """
    Setter Levert=1 for gitt utlån hvis det eksisterer og ikke allerede er levert.
    """
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT Levert FROM utlån WHERE UtlånsNr = %s",
            (utlansnr,),
        )
        row = cur.fetchone()
        if row is None:
            print(f"Ingen utlån funnet med UtlånsNr={utlansnr}.")
            cur.close()
            return

        levert = row[0]
        if levert == 1:
            print("Utlånet er allerede registrert som levert.")
            cur.close()
            return

        cur.execute(
            "UPDATE utlån SET Levert = 1 WHERE UtlånsNr = %s",
            (utlansnr,),
        )
        conn.commit()
        print("Bok er registrert som levert.")
        cur.close()
    except Error as e:
        conn.rollback()
        print(f"Feil ved levering: {e}")


def vis_historikk(conn, lnr: int):
    """
    Viser alle utlån for en låner, med bokinfo og status.
    """
    sql = """
          SELECT u.UtlånsNr,
                 b.Tittel,
                 b.Forfatter,
                 u.Utlånsdato,
                 CASE WHEN u.Levert = 1 THEN 'Levert' ELSE 'Utlånt' END AS Status
          FROM utlån u
                   JOIN eksemplar e ON (u.ISBN = e.ISBN AND u.EksNr = e.EksNr)
                   JOIN bok b ON b.ISBN = u.ISBN
          WHERE u.LNr = %s
          ORDER BY u.Utlånsdato DESC, u.UtlånsNr DESC \
          """
    cur = conn.cursor()
    cur.execute("SELECT Fornavn, Etternavn, Adresse FROM låner WHERE LNr = %s", (lnr,))
    ln = cur.fetchone()
    if ln is None:
        print(f"Låner med LNr={lnr} finnes ikke.")
        cur.close()
        return

    fornavn, etternavn, adresse = ln
    cur.execute(sql, (lnr,))
    rows = cur.fetchall()
    print(f"Låner: {fornavn} {etternavn} (LNr={lnr}) – Adresse: {adresse}")
    _print_table(["UtlånsNr", "Tittel", "Forfatter", "Utlånsdato", "Status"], rows)
    cur.close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser():
    db_parent = get_db_args()

    parser = argparse.ArgumentParser(
        description="Bibliotek-CLI for Oppgave 4 (MySQL)",
        parents=[db_parent],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    sub = parser.add_subparsers(dest="cmd")

    # vis-alle
    p1 = sub.add_parser("vis-alle", help="Vis alle bøker", parents=[db_parent])
    p1.set_defaults(func=lambda ns: vis_alle_boker(connect_to_database(ns)))

    # søk
    p2 = sub.add_parser("sok", help="Søk i tittel/forfatter", parents=[db_parent])
    p2.add_argument("--tekst", required=True, help="Søkestreng")
    p2.set_defaults(func=lambda ns: sok_bok(connect_to_database(ns), ns.tekst))

    # registrer utlån
    p3 = sub.add_parser("registrer-utlan", help="Registrer nytt utlån", parents=[db_parent])
    p3.add_argument("--lnr", type=int, required=True, help="Lånernummer")
    p3.add_argument("--isbn", required=True)
    p3.add_argument("--eksnr", type=int, required=True)
    p3.add_argument("--utlansdato", required=False, help="YYYY-MM-DD; hvis utelatt brukes dagens dato")
    p3.set_defaults(func=lambda ns: registrer_utlan(connect_to_database(ns), ns.lnr, ns.isbn, ns.eksnr, ns.utlansdato))

    # lever bok
    p4 = sub.add_parser("lever-bok", help="Registrer levering av bok", parents=[db_parent])
    p4.add_argument("--utlansnr", type=int, required=True)
    p4.set_defaults(func=lambda ns: lever_bok(connect_to_database(ns), ns.utlansnr))

    # historikk
    p5 = sub.add_parser("historikk", help="Vis utlånshistorikk for en låner", parents=[db_parent])
    p5.add_argument("--lnr", type=int, required=True)
    p5.set_defaults(func=lambda ns: vis_historikk(connect_to_database(ns), ns.lnr))

    return parser


def main():
    parser = build_parser()
    # Hvis ingen delkommando er gitt: standard = vis-alle
    if len(sys.argv) == 1 or (len(sys.argv) > 1 and sys.argv[1].startswith("--")):
        # Parse DB-arg fra sys.argv (kan bare være --host/--user osv.)
        ns, _ = parser.parse_known_args()
        conn = connect_to_database(ns)
        vis_alle_boker(conn)
        conn.close()
        return

    ns = parser.parse_args()
    # Kjør valgt funksjon
    if hasattr(ns, "func"):
        ns.func(ns)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
