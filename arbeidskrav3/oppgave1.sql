/*
====================================================================
    MERKNAD (VIDEOFORKLARING)

    I videoen kjørte jeg først databaseoppsettet fra Arbeidskrav 2.
    Dette er fordi normaliseringsdelen i Oppgave 1B bruker data
    fra den gamle tabellen "bok" (for eksempel: SELECT DISTINCT Forfatter FROM bok).

    For at migreringen og normaliseringen skal fungere riktig,
    må den opprinnelige strukturen (bok, eksemplar, låner, utlån)
    opprettes før Oppgave 1B kjøres.

    Koden nedenfor er derfor inkludert både som dokumentasjon
    og fordi den må kjøres før normaliseringen.
====================================================================
*/

-- OPPGAVE 1: Bibliotek-database

-- Oppretter databasen med riktig tegnsett og sortering
DROP
DATABASE IF EXISTS ga_bibliotek;
CREATE
DATABASE IF NOT EXISTS ga_bibliotek;
ALTER
DATABASE ga_bibliotek CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Velger databasen som skal brukes
USE
ga_bibliotek;

-- Oppretter tabellen "bok" (grunnleggende bokinformasjon)
CREATE TABLE `bok`
(
    `ISBN`        VARCHAR(13) PRIMARY KEY,
    `Tittel`      VARCHAR(255) NOT NULL,
    `Forfatter`   VARCHAR(100) NOT NULL,
    `Forlag`      VARCHAR(100) NOT NULL,
    `UtgittÅr`    INT          NOT NULL,
    `AntallSider` INT          NOT NULL
) ENGINE=InnoDB;

-- Oppretter tabellen "eksemplar" (hvert fysisk eksemplar av en bok)
CREATE TABLE `eksemplar`
(
    `ISBN`  VARCHAR(13) NOT NULL,
    `EksNr` INT         NOT NULL,
    PRIMARY KEY (`ISBN`, `EksNr`),
    CONSTRAINT `fk_eksemplar_bok`
        FOREIGN KEY (`ISBN`) REFERENCES `bok` (`ISBN`)
            ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Oppretter tabellen "låner" (personer som låner bøker)
CREATE TABLE `låner`
(
    `LNr`       INT AUTO_INCREMENT PRIMARY KEY,
    `Fornavn`   VARCHAR(100) NOT NULL,
    `Etternavn` VARCHAR(100) NOT NULL,
    `Adresse`   VARCHAR(255) NOT NULL
) ENGINE=InnoDB;

-- Oppretter tabellen "utlån" (registrerer utlån og leveringsstatus)
CREATE TABLE `utlån`
(
    `UtlånsNr`   INT AUTO_INCREMENT PRIMARY KEY,
    `ISBN`       VARCHAR(13) NOT NULL,
    `EksNr`      INT         NOT NULL,
    `LNr`        INT         NOT NULL,
    `Utlånsdato` DATE        NOT NULL,
    `Levert`     TINYINT     NOT NULL,
    CONSTRAINT `fk_utlån_eksemplar`
        FOREIGN KEY (`ISBN`, `EksNr`) REFERENCES `eksemplar` (`ISBN`, `EksNr`)
            ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_utlån_låner`
        FOREIGN KEY (`LNr`) REFERENCES `låner` (`LNr`)
            ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `chk_utlån_levert` CHECK (`Levert` IN (0, 1))
) ENGINE=InnoDB;

-- Legger inn eksempeldata i "bok"
INSERT INTO `bok` (`ISBN`, `Tittel`, `Forfatter`, `Forlag`, `UtgittÅr`, `AntallSider`)
VALUES ('9788205342291', 'Forvandlingen', 'Franz Kafka', 'Gyldendal', 1915, 88),
       ('9000000000001', 'Sult', 'Knut Hamsun', 'Gyldendal', 1890, 200),
       ('9000000000002', 'Et dukkehjem', 'Henrik Ibsen', 'Aschehoug', 1879, 120),
       ('9000000000003', 'Kürk Mantolu Madonna', 'Sabahattin Ali', 'YKY', 1943, 160),
       ('9000000000004', 'Kar', 'Orhan Pamuk', 'İletişim', 2002, 460),
       ('9000000000005', 'Suç og Ceza', 'Fyodor Dostoyevski', 'Eksmo', 1866, 545),
       ('9000000000006', 'Savaş og Barış', 'Lev Tolstoy', 'Penguin', 1869, 1225),
       ('9000000000007', 'Pride and Prejudice', 'Jane Austen', 'T. Egerton', 1813, 279),
       ('9000000000008', 'One Hundred Years of Solitude', 'Gabriel García Márquez', 'Harper & Row', 1967, 417),
       ('9000000000009', 'Les Misérables', 'Victor Hugo', 'A. Lacroix', 1862, 1232);

-- Legger inn eksempeldata i "eksemplar"
INSERT INTO `eksemplar` (`ISBN`, `EksNr`)
VALUES ('9788205342291', 1),
       ('9000000000001', 1),
       ('9000000000002', 1),
       ('9000000000003', 1),
       ('9000000000004', 1),
       ('9000000000005', 1),
       ('9000000000006', 1),
       ('9000000000007', 1),
       ('9000000000008', 1),
       ('9000000000009', 1);

-- Legger inn eksempeldata i "låner"
INSERT INTO `låner` (`Fornavn`, `Etternavn`, `Adresse`)
VALUES ('Vincent', 'van Gogh', 'Zundert'),
       ('Sabahattin', 'Ali', 'Edirne'),
       ('Edvard', 'Munch', 'Oslo'),
       ('Harriet', 'Backer', 'Holmestrand'),
       ('Pablo', 'Picasso', 'Málaga');

-- Registrerer ett eksempelutlån (ikke levert ennå)
INSERT INTO `utlån` (`ISBN`, `EksNr`, `LNr`, `Utlånsdato`, `Levert`)
VALUES ('9788205342291', 1, 2, '2025-10-29', 0);

-- Ytelsesforbedrende indekser for hyppig brukte kolonner
CREATE INDEX idx_eksemplar_isbn ON eksemplar (ISBN);
CREATE INDEX idx_utlan_isbn_eksnr ON utlån (ISBN, EksNr);
CREATE INDEX idx_utlan_lnr ON utlån (LNr);
CREATE INDEX idx_bok_forfatter ON bok (Forfatter);

-- (Her slutter "Arbeidskrav 2" delen — neste del starter Oppgave 1A-1B)

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
-- Før jeg starter med tabellene setter jeg tegnsettet til UTF8MB4 og velger databasen ga_bibliotek.
-- Dette sikrer riktig håndtering av norske tegn og at alle tabellene blir opprettet i riktig database.
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
