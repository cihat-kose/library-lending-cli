# Avansert Kalkulator – README
Arbeidskrav 3 – Oppgave 3

Dette prosjektet inneholder løsningen til Oppgave 3 i Arbeidskrav 3. Programmet er en menybasert kalkulator skrevet i Python og ligger i filen:

```
arbeidskrav3/oppgave3_kalkulator.py
```

## Funksjonalitet
Kalkulatoren støtter følgende operasjoner:
1. Addisjon  
2. Subtraksjon  
3. Multiplikasjon  
4. Divisjon (med sjekk mot null)  
5. Potens  
6. Kvadratrot (ikke-definert for negative tall)  
7. Avslutt programmet  

Programmet kjører i en løkke til brukeren velger alternativ 7.

## Programstruktur
Koden er organisert i funksjoner:
- `les_tall()` håndterer trygg innlesing av tall.  
- Én funksjon per operasjon: `addisjon()`, `subtraksjon()`, `multiplikasjon()`, `divisjon()`, `potens()`, `kvadratrot()`.  
- `skriv_meny()` viser menyen.  
- `main()` styrer programflyten.

## Kjøre instruksjoner
Programmet krever kun standardbiblioteket `math`.

Fra prosjektets rotmappe:
```
python .\arbeidskrav3\oppgave3_kalkulator.py
```
Eller gå inn i mappen og kjør:
```
cd arbeidskrav3
python oppgave3_kalkulator.py
```

## Filstruktur
```
gokstadakademiet-arbeidskrav3/
 ├── arbeidskrav2/
 └── arbeidskrav3/
      ├── Arbeidskrav3Backend-14-11-2025.pdf
      ├── oppgave1.sql
      ├── oppgave3_kalkulator.py
      └── README.md
```

## Bruk av KI
- KI ble brukt for å få oppgaven forklart tydeligere.  
- Etter at koden var skrevet, ble KI brukt til å sammenligne alternative løsninger og kvalitetssikre strukturen.  
- KI ble brukt for å sikre at kravene i oppgaveteksten ble fulgt.  
- KI ble brukt til å utforme denne README-filen.

## Oppsummering
Programmet oppfyller kravene, har tydelig struktur og håndterer feil korrekt.
