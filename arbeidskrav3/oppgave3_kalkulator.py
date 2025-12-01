#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Oppgave 3 – Avansert kalkulator
Programmet bruker en enkel meny og grunnleggende kontrollstrukturer.
Alle beregninger gjøres i egne funksjoner for ryddighet og gjenbruk.
Ingen ekstra konfigurasjon er nødvendig – programmet kan kjøres direkte.
"""

import math

def les_tall(tekst):
    """Leser et tall fra brukeren og håndterer ugyldig input."""
    while True:
        try:
            return float(input(tekst))
        except ValueError:
            print("Ugyldig tall. Prøv igjen.")

def addisjon():
    """Utfører addisjon av to tall."""
    a = les_tall("Skriv inn første tall: ")
    b = les_tall("Skriv inn andre tall: ")
    print(f"Resultat: {a} + {b} = {a + b}\n")

def subtraksjon():
    """Utfører subtraksjon av to tall."""
    a = les_tall("Skriv inn første tall: ")
    b = les_tall("Skriv inn andre tall: ")
    print(f"Resultat: {a} - {b} = {a - b}\n")

def multiplikasjon():
    """Utfører multiplikasjon av to tall."""
    a = les_tall("Skriv inn første tall: ")
    b = les_tall("Skriv inn andre tall: ")
    print(f"Resultat: {a} * {b} = {a * b}\n")

def divisjon():
    """Utfører divisjon med sjekk mot deling på null."""
    a = les_tall("Skriv inn telleren: ")
    b = les_tall("Skriv inn nevneren: ")
    if b == 0:
        print("Kan ikke dele på null.\n")
    else:
        print(f"Resultat: {a} / {b} = {a / b}\n")

def potens():
    """Beregner x opphøyd i y."""
    a = les_tall("Skriv inn grunnverdi (x): ")
    b = les_tall("Skriv inn eksponent (y): ")
    print(f"Resultat: {a} ^ {b} = {a ** b}\n")

def kvadratrot():
    """Beregner kvadratroten av et tall, hvis tallet er ikke-negativt."""
    a = les_tall("Skriv inn tallet: ")
    if a < 0:
        print("Kan ikke ta kvadratroten av et negativt tall.\n")
    else:
        print(f"Resultat: √{a} = {math.sqrt(a)}\n")

def skriv_meny():
    """Viser kalkulatorens meny."""
    print("=== Avansert kalkulator ===")
    print("1. Addisjon")
    print("2. Subtraksjon")
    print("3. Multiplikasjon")
    print("4. Divisjon")
    print("5. Potens")
    print("6. Kvadratrot")
    print("7. Avslutt")

def main():
    """Programløkken som håndterer menyvalg og funksjonskall."""
    while True:
        skriv_meny()
        valg = input("Velg et alternativ (1-7): ").strip()

        if valg == "1":
            addisjon()
        elif valg == "2":
            subtraksjon()
        elif valg == "3":
            multiplikasjon()
        elif valg == "4":
            divisjon()
        elif valg == "5":
            potens()
        elif valg == "6":
            kvadratrot()
        elif valg == "7":
            print("Avslutter programmet. Takk for bruk!")
            break
        else:
            print("Ugyldig valg. Skriv inn et tall mellom 1 og 7.\n")

if __name__ == "__main__":
    main()
