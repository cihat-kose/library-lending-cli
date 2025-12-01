# Arbeidskrav 2 – Backend (Databaser og Python)

**Kandidat:** Cihat Köse  
**Fag:** Backend-programmering (Databaser og Python)  

---

## Oppgave 1 – Databasestruktur og innhold

I denne oppgaven ble databasen `ga_bibliotek` opprettet med følgende tabeller:

1. **bok**  
   - Primærnøkkel: `ISBN`  
   - Felter: `ISBN`, `Tittel`, `Forfatter`, `AntallSider`, `UtgittÅr`  
   - Beskrivelse: Inneholder informasjon om alle bøker i biblioteket.

2. **eksemplar**  
   - Primærnøkkel: (`ISBN`, `EksNr`)  
   - Fremmednøkkel: `ISBN` → `bok(ISBN)`  
   - Beskrivelse: Representerer fysiske eksemplarer av bøker.

3. **låner**  
   - Primærnøkkel: `LNr` (AUTO_INCREMENT)  
   - Felter: `Fornavn`, `Etternavn`, `Adresse`, `Postnr`, `Poststed`  
   - Beskrivelse: Inneholder informasjon om lånerne.

4. **utlån**  
   - Primærnøkkel: `UtlånsNr` (AUTO_INCREMENT)  
   - Fremmednøkler:  
     - (`ISBN`, `EksNr`) → `eksemplar(ISBN, EksNr)`  
     - `LNr` → `låner(LNr)`  
   - Feltet `Levert` har **CHECK (Levert IN (0,1))** for dataintegritet.

### Ekstra tiltak
- Alle tabeller bruker **utf8mb4_unicode_ci** for Unicode-støtte.
- Det er lagt til indekser på kolonner som brukes i JOIN-operasjoner for ytelse.

---

## Oppgave 2 – Datamodell og forklaring

### Datamodell (ER-diagram)
ER-skjemaet beskriver relasjonene mellom tabellene:

📎 *Se vedlagte fil:* `oppgave2_skjema.png`

### Forklaring av tabeller og nøkler

| Tabell | Primærnøkkel | Fremmednøkler | Kommentar |
|--------|---------------|----------------|------------|
| **bok** | ISBN | – | Alle bøker i systemet |
| **eksemplar** | ISBN, EksNr | bok(ISBN) | Fysiske eksemplarer |
| **låner** | LNr | – | Registrerte lånere |
| **utlån** | UtlånsNr | eksemplar, låner | Oversikt over utlån |

- Databasen følger **3NF (Tredje normalform)**.  
- Det er **referanseintegritet** gjennom FK-koblinger.  
- **CHECK**, **AUTO_INCREMENT** og **NOT NULL** brukes konsekvent.

---

## Oppgave 3 – SQL-spørringer

`oppgave3.sql` inneholder 12 spørringer som dekker følgende krav:

1. Vis alle bøker utgitt etter år 2000  
2. Vis forfatter og tittel, sortert alfabetisk etter forfatter  
3. Vis bøker med mer enn 300 sider  
4. Sett inn ny bok  
5. Registrer ny låner  
6. Oppdater adresse til en låner  
7. Vis utlån med lånernavn og boktittel  
8. Antall eksemplarer per bok  
9. Antall utlån per låner (inkludert 0)  
10. Antall utlån per bok  
11. Bøker som aldri har vært utlånt  
12. Forfatter og totalt antall utlån

Alle spørringer er testet mot databasen og returnerer riktige resultater.

---

## Oppgave 4 – Python-program (MySQL Connector)

**Fil:** `oppgave4.py`

Programmet gir et kommandolinjegrensesnitt (CLI) for å administrere biblioteket.  
Alle databaseoperasjoner bruker `mysql.connector` med parameteriserte spørringer for å unngå SQL-injeksjon.

### Funksjoner

| Funksjon | Beskrivelse |
|-----------|--------------|
| `connect_to_database()` | Oppretter forbindelse til MySQL. Feilhåndtering inkludert. |
| `vis_alle_boker()` | Viser alle bøker. (standardhandling uten argumenter) |
| `sok_bok(tekst)` | Søker i tittel/forfatter. |
| `registrer_utlan(isbn, eksnr, lnr)` | Oppretter nytt utlån dersom låner og eksemplar finnes og ikke allerede er utlånt. |
| `lever_bok(utlansnr)` | Marker utlån som levert (hvis ikke allerede). |
| `vis_lanerhistorikk(lnr)` | Viser historikk over lånerens utlån. |

### Eksempel på bruk

```bash
# Kjør med argumenter
python oppgave4.py vis-alle
python oppgave4.py sok --tekst "Ibsen"
python oppgave4.py registrer-utlan --isbn 9000000000001 --eksnr 1 --lnr 3
python oppgave4.py lever-bok --utlansnr 5
python oppgave4.py historikk --lnr 3
```

### UX-forbedringer
- Programmet kan kjøres **uten argumenter**, og viser da automatisk alle bøker.  
- Klare feilmeldinger for ugyldige låner-IDer eller eksemplarer.  
- `Levert` kontrolleres før oppdatering for å unngå duplikate leveringer.

---

## ⚙Konfigurasjon og miljøvariabler

Programmet støtter både kommandolinjeargumenter og miljøvariabler.  
Dersom du ikke spesifiserer argumenter, leses følgende miljøvariabler automatisk:

```bash
export DB_HOST=127.0.0.1
export DB_PORT=3306
export DB_USER=root
export DB_PASSWORD=******
export DB_NAME=ga_bibliotek
```

Deretter kan du kjøre:
```bash
python oppgave4.py
```

---

## Installasjon

Krever Python 3.10+ og MySQL-server.  
Installer nødvendige pakker:

```bash
pip install -r requirements.txt
```

**requirements.txt:**
```
mysql-connector-python
```

---

## Filoversikt

| Filnavn | Beskrivelse |
|----------|-------------|
| `oppgave1.sql` | Opprettelse av database, tabeller og eksempeldata |
| `oppgave2_skjema.png` | ER-diagram for databasen |
| `oppgave3.sql` | SQL-spørringer (12 stk) |
| `oppgave4.py` | Python-program med CLI |
| `requirements.txt` | Avhengigheter |
| `README.md` | Dokumentasjon (denne filen) |
| `Arbeidskrav2Backend-17-10-2025.pdf` | Oppgavetekst (referanse) |

---

## Oppsummering

| Deloppgave | Innhold | Status |
|-------------|----------|---------|
| Oppgave 1 | Databasestruktur og eksempeldata | ✅ |
| Oppgave 2 | Datamodell og forklaring | ✅ |
| Oppgave 3 | 12 SQL-spørringer | ✅ |
| Oppgave 4 | Python-program med databaseintegrasjon | ✅ |
| README / Dokumentasjon | Fullstendig og i henhold til retningslinjer | ✅ |

---

**Arbeidskravet er gjennomført i samsvar med veiledningen og demonstrerer funksjonell databaseintegrasjon mellom SQL og Python.**
