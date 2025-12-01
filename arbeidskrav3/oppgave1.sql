-- ===== OPPGAVE 1A – Evaluering av tabellen 'bok_utvidet' =====

-- Tabellen 'bok_utvidet' inneholder bok-, forfatter- og forlagsinformasjon i én tabell.
-- Dette skaper flere problemer:

-- 1) Redundans:
--    Forfatter- og forlagsdata gjentas for hver bok, noe som fører til unødvendig duplisering.

-- 2) Oppdateringsanomalier:
--    Endringer i forfatter- eller forlagsinformasjon må oppdateres i flere rader.
--    Hvis én rad ikke oppdateres, oppstår inkonsistente data.

-- 3) Slettingsanomalier:
--    Sletting av en bok kan føre til utilsiktet tap av informasjon om forfatter eller forlag.

-- 4) Innsettingsanomalier:
--    Man kan ikke registrere en ny forfatter eller et nytt forlag uten å registrere en bok,
--    fordi tabellen mangler egne entiteter.

-- 5) Brudd på tredje normalform (3NF):
--    Tabellen inneholder flere uavhengige entiteter (bok, forfatter, forlag).
--    Ikke-nøkkelattributter avhenger ikke kun av primærnøkkelen.
--    Dette bryter normaliseringsprinsippene.

-- Konklusjon:
-- 'bok_utvidet' bør deles opp i separate tabeller for bok, forfatter og forlag
-- for å redusere redundans og unngå anomalier.


-- ===== OPPGAVE 1B – Design av normaliserte tabeller =====

-- Målet er å etablere en tabellstruktur som oppfyller 3NF.
-- De uavhengige entitetene separeres slik:
--   • forfatter       – lagrer informasjon om forfattere
--   • forlag          – lagrer informasjon om forlag
--   • bok_normalisert – inneholder bokspesifikke data og referanser til forfatter og forlag
--
-- Denne strukturen reduserer redundans, og fremmednøkler sikrer referanseintegritet.


-- ===== SQL-SCRIPT FOR NORMALISERT STRUKTUR =====

-- Tegnsett (norske tegn)
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;
SET COLLATION_CONNECTION = 'utf8mb4_unicode_ci';

-- Velg database
USE ga_bibliotek;


-- Trinn 1: Opprett tabellen for forfatter
CREATE TABLE IF NOT EXISTS forfatter (
  ForfatterID INT AUTO_INCREMENT PRIMARY KEY,
  Navn VARCHAR(200) NOT NULL,
  Fødselsår INT NULL,
  Land VARCHAR(100) NULL,
  UNIQUE KEY ux_forfatter_navn (Navn)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Trinn 2: Opprett tabellen forlag
CREATE TABLE IF NOT EXISTS forlag (
  ForlagID INT AUTO_INCREMENT PRIMARY KEY,
  Navn VARCHAR(200) NOT NULL,
  Adresse VARCHAR(255) NULL,
  UNIQUE KEY ux_forlag_navn (Navn)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Trinn 3: Opprett normalisert bok-tabell
CREATE TABLE IF NOT EXISTS bok_normalisert (
  ISBN VARCHAR(13) PRIMARY KEY,
  Tittel VARCHAR(255) NOT NULL,
  ForfatterID INT NOT NULL,
  ForlagID INT NOT NULL,
  UtgittÅr INT NOT NULL,
  AntallSider INT NOT NULL,

  CONSTRAINT fk_bok_forfatter FOREIGN KEY (ForfatterID)
    REFERENCES forfatter(ForfatterID)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,

  CONSTRAINT fk_bok_forlag FOREIGN KEY (ForlagID)
    REFERENCES forlag(ForlagID)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Trinn 4: Opprett tabeller for eksemplar, låner og utlån
CREATE TABLE IF NOT EXISTS eksemplar (
  ISBN VARCHAR(13) NOT NULL,
  EksNr INT NOT NULL,
  PRIMARY KEY (ISBN, EksNr),
  CONSTRAINT fk_eksemplar_bok FOREIGN KEY (ISBN)
    REFERENCES bok_normalisert(ISBN)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS låner (
  LNr INT AUTO_INCREMENT PRIMARY KEY,
  Fornavn VARCHAR(100) NOT NULL,
  Etternavn VARCHAR(100) NOT NULL,
  Adresse VARCHAR(255) NULL,
  Postnr VARCHAR(20) NULL,
  Poststed VARCHAR(100) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS utlån (
  UtlånsNr INT AUTO_INCREMENT PRIMARY KEY,
  ISBN VARCHAR(13) NOT NULL,
  EksNr INT NOT NULL,
  LNr INT NOT NULL,
  Utlånsdato DATE NOT NULL,
  Levert TINYINT NOT NULL DEFAULT 0,

  CONSTRAINT fk_utlån_eksemplar FOREIGN KEY (ISBN, EksNr)
    REFERENCES eksemplar(ISBN, EksNr)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,

  CONSTRAINT fk_utlån_låner FOREIGN KEY (LNr)
    REFERENCES låner(LNr)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,

  CONSTRAINT chk_utlån_levert CHECK (Levert IN (0,1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Trinn 5: Migrer forfattere fra eksisterende bok-tabell
INSERT IGNORE INTO forfatter (Navn)
SELECT DISTINCT Forfatter
FROM bok
WHERE Forfatter IS NOT NULL AND Forfatter <> '';


-- Trinn 6: Migrer forlag fra eksisterende bok-tabell
INSERT IGNORE INTO forlag (Navn)
SELECT DISTINCT Forlag
FROM bok
WHERE Forlag IS NOT NULL AND Forlag <> '';


-- Trinn 7: Migrer bøker til normalisert tabell
INSERT INTO bok_normalisert (ISBN, Tittel, ForfatterID, ForlagID, UtgittÅr, AntallSider)
SELECT
  b.ISBN,
  b.Tittel,
  f.ForfatterID,
  g.ForlagID,
  b.UtgittÅr,
  b.AntallSider
FROM bok AS b
JOIN forfatter AS f ON TRIM(LOWER(f.Navn)) = TRIM(LOWER(b.Forfatter))
JOIN forlag AS g ON TRIM(LOWER(g.Navn)) = TRIM(LOWER(b.Forlag));


-- Trinn 8: Kontrollspørringer

-- Antall bøker i ny tabell
SELECT COUNT(*) AS antall_bøker FROM bok_normalisert;

-- Antall forfattere og forlag
SELECT 'forfatter' AS tabell, COUNT(*) AS antall FROM forfatter
UNION ALL
SELECT 'forlag', COUNT(*) FROM forlag;

-- Poster som mangler korrekt matching
SELECT b.ISBN, b.Tittel, b.Forfatter, f.ForfatterID, b.Forlag, g.ForlagID
FROM bok b
LEFT JOIN forfatter f ON TRIM(f.Navn) = TRIM(b.Forfatter)
LEFT JOIN forlag g ON TRIM(g.Navn) = TRIM(b.Forlag)
WHERE f.ForfatterID IS NULL OR g.ForlagID IS NULL;


-- Trinn 9: Eksempelsøk (demo) -- Vis noen normaliserte bokposter med forfatter og forlag for verifikasjon
SELECT
  b.ISBN,
  b.Tittel,
  f.Navn AS Forfatter,
  g.Navn AS Forlag,
  b.UtgittÅr,
  b.AntallSider
FROM bok_normalisert b
JOIN forfatter f ON b.ForfatterID = f.ForfatterID
JOIN forlag g ON b.ForlagID = g.ForlagID
LIMIT 10;
