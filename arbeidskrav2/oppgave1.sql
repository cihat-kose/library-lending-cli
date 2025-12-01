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
