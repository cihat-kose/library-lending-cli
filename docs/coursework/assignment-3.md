# 📘 Gokstad Akademiet – Arbeidskrav 3  
## Oppgave 3 – Python Kalkulator

Dette prosjektet inneholder løsningen til **Oppgave 3** i Arbeidskrav 3. Programmet er en menybasert kalkulator skrevet i Python og ligger i filen:

```
arbeidskrav3/oppgave3_kalkulator.py
```

---

## 🔧 Funksjonalitet

Kalkulatoren støtter følgende operasjoner:

1. **Addisjon**  
2. **Subtraksjon**  
3. **Multiplikasjon**  
4. **Divisjon** (inkluderer sjekk mot deling på null)  
5. **Potens**  
6. **Kvadratrot** (ikke definert for negative tall)  
7. **Avslutt programmet**

Programmet kjører i en løkke helt til brukeren velger alternativ **7**.

---

## 🧱 Programstruktur

Koden er organisert i funksjoner for å gjøre strukturen tydelig og enkel å vedlikeholde.
Hver funksjon **leser selv inn tall fra brukeren**, akkurat slik det er implementert i programmet.

* `les_tall()` – Trygg innlesing av tall fra bruker
* `addisjon()` – Leser inn to tall og skriver ut summen
* `subtraksjon()` – Leser inn to tall og beregner differansen
* `multiplikasjon()` – Leser inn to tall og multipliserer dem
* `divisjon()` – Leser inn to tall og håndterer deling på null
* `potens()` – Leser inn base og eksponent, beregner potensen
* `kvadratrot()` – Leser inn ett tall og beregner kvadratroten (kun for ikke-negative tall)
* `skriv_meny()` – Viser menyvalg
* `main()` – Styrer programflyten og håndterer brukerens valg

---

## ▶️ Kjøreprogram

Programmet krever kun standardbiblioteket **math**.

Kjør fra rotmappen:

```bash
python .\arbeidskrav3\oppgave3_kalkulator.py
```

Eller:

```bash
cd arbeidskrav3
python oppgave3_kalkulator.py
```

---

## 📂 Filstruktur

```
gokstadakademiet-arbeidskrav3/
 ├── arbeidskrav2/
 └── arbeidskrav3/
      ├── Arbeidskrav3Backend-14-11-2025.pdf
      ├── oppgave1.sql
      ├── oppgave3_kalkulator.py
      └── README.md
```

---

## 🤖 Bruk av KI (Kunstig Intelligens)

I dette arbeidet ble KI-verktøy som *ChatGPT*, *Claude Haiku*, *Llama 4 Scout* og *Mistral Small* brukt som støtte.  
Formålet med KI-bruken var:

- Å forstå oppgavebeskrivelsene bedre (da norsk ikke er morsmål)  
- Å sammenligne alternative løsninger og sikre god struktur  
- Å kontrollere at løsningen tilfredsstiller kravene  
- Å få hjelp til formidling og strukturering av forklaringstekster  
- Å utforme README-filen på en ryddig og profesjonell måte  

**KI ble brukt som støtte til læring og forklaring.  
Alle faglige vurderinger og løsninger er mine egne, og ingenting er inkludert uten at jeg forstår det fullt ut.**

---

## ✅ Oppsummering

Programmet:

- Oppfyller alle krav i oppgaveteksten  
- Har tydelig struktur  
- Inneholder robuste feilsjekker  
- Har en brukervennlig meny  
- Er enkelt å videreutvikle og vedlikeholde  
