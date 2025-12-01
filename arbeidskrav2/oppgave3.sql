-- OPPGAVE 3: SQL-spørringer

-- 1) Alle bøker publisert etter år 2000
SELECT ISBN, Tittel, Forfatter, UtgittÅr
FROM bok
WHERE UtgittÅr > 2000
ORDER BY UtgittÅr DESC, Tittel;

-- 2) Forfatter og tittel på alle bøker, sortert alfabetisk etter forfatter (så tittel)
SELECT Forfatter, Tittel
FROM bok
ORDER BY Forfatter ASC, Tittel ASC;

-- 3) Alle bøker med mer enn 300 sider
SELECT ISBN, Tittel, AntallSider
FROM bok
WHERE AntallSider > 300
ORDER BY AntallSider DESC;

-- 4) Legg til en ny bok i 'bok'
INSERT INTO bok (ISBN, Tittel, Forfatter, Forlag, UtgittÅr, AntallSider)
VALUES ('9000000000010', 'Brødrene Karamazov', 'Fjodor Dostojevskij', 'Aschehoug', 1880, 824);

-- 5) Legg til en ny låner i 'låner'
INSERT INTO låner (Fornavn, Etternavn, Adresse)
VALUES ('Kari', 'Nordmann', 'Trondheim');

-- 6) Oppdater adresse for en spesifikk låner (eksempel: LNr = 3)
UPDATE låner
SET Adresse = 'Tøyengata 12, 0578 Oslo'
WHERE LNr = 3;

-- 7) Alle utlån med lånerens navn og boktittel
SELECT u.UtlånsNr, u.Utlånsdato, l.Fornavn, l.Etternavn, b.Tittel
FROM utlån u
JOIN låner l     ON l.LNr = u.LNr
JOIN eksemplar e ON e.ISBN = u.ISBN AND e.EksNr = u.EksNr
JOIN bok b       ON b.ISBN = e.ISBN
ORDER BY u.Utlånsdato DESC, u.UtlånsNr DESC;

-- 8) Alle bøker og antall eksemplarer for hver bok
SELECT b.ISBN, b.Tittel, COUNT(e.EksNr) AS AntallEksemplarer
FROM bok b
LEFT JOIN eksemplar e ON e.ISBN = b.ISBN
GROUP BY b.ISBN, b.Tittel
ORDER BY AntallEksemplarer DESC, b.Tittel;

-- 9) Antall utlån per låner (inkluder låner uten utlån)
SELECT l.LNr, l.Fornavn, l.Etternavn, COUNT(u.UtlånsNr) AS AntallUtlån
FROM låner l
LEFT JOIN utlån u ON u.LNr = l.LNr
GROUP BY l.LNr, l.Fornavn, l.Etternavn
ORDER BY AntallUtlån DESC, l.Etternavn, l.Fornavn;

-- 10) Antall utlån per bok
SELECT b.ISBN, b.Tittel, COUNT(u.UtlånsNr) AS AntallUtlån
FROM bok b
LEFT JOIN eksemplar e ON e.ISBN = b.ISBN
LEFT JOIN utlån u ON u.ISBN = e.ISBN AND u.EksNr = e.EksNr
GROUP BY b.ISBN, b.Tittel
ORDER BY AntallUtlån DESC, b.Tittel;

-- 11) Alle bøker som ikke har blitt lånt ut
SELECT b.ISBN, b.Tittel
FROM bok b
LEFT JOIN eksemplar e ON e.ISBN = b.ISBN
LEFT JOIN utlån u ON u.ISBN = e.ISBN AND u.EksNr = e.EksNr
WHERE u.UtlånsNr IS NULL
GROUP BY b.ISBN, b.Tittel
ORDER BY b.Tittel;

-- 12) Forfatter og antall utlånte bøker per forfatter
SELECT b.Forfatter, COUNT(u.UtlånsNr) AS AntallUtlån
FROM bok b
LEFT JOIN eksemplar e ON e.ISBN = b.ISBN
LEFT JOIN utlån u ON u.ISBN = e.ISBN AND u.EksNr = e.EksNr
GROUP BY b.Forfatter
ORDER BY AntallUtlån DESC, b.Forfatter;


-- (Ekstra) Alternativ for spørring 11 med NOT EXISTS (samme resultat):
-- Viser bøker som aldri har vært utlånt (uavhengig av antall eksemplarer)
SELECT b.ISBN, b.Tittel
FROM bok b
WHERE NOT EXISTS (
  SELECT 1
  FROM eksemplar e
  JOIN utlån u ON u.ISBN = e.ISBN AND u.EksNr = e.EksNr
  WHERE e.ISBN = b.ISBN
)
ORDER BY b.Tittel;
