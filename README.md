# REPHUB – Kalkulator dawek paszowych

Nowoczesna aplikacja KivyMD dla hodowców bydła mlecznego i opasowego. Projekt został
zrealizowany modułowo zgodnie z siedmiostopniowym planem: zarządzanie bazą pasz,
obliczenia wartości pokarmowych, panel hodowcy, interfejs graficzny, zapisywanie i
porównywanie dawek, walidacja oraz tryb testera końcowego.

## Przegląd modułów

1. **Zarządzanie paszami** – referencyjna baza pasz, dodawanie i edycja danych, zarządzanie
   dawką bieżącą.
2. **Obliczenia żywieniowe** – analizy suchej masy, białka, energii i włókna z obsługą braków
   danych.
3. **Panel hodowcy** – projekcje logistyczne dla stada, liczba załadunków i wystarczalność
   zapasów.
4. **Interfejs KivyMD** – aplikacja desktopowa z zakładkami dla dawki, panelu hodowcy i
   zapisanych dawek.
5. **Zapisywanie i porównania** – trwałe przechowywanie dawek w JSON oraz karty porównawcze.
6. **Walidacja danych** – wychwytywanie błędnych wartości i bezpieczne zastępowanie ich w
   obliczeniach.
7. **Tryb testera końcowego** – automatyczny scenariusz przechodzący przez wszystkie funkcje,
   ułatwiający testy końcowe.

## Wymagania

* Python 3.10+
* Pip oraz opcjonalnie wirtualne środowisko (`venv`)

## Instalacja i uruchomienie

1. **Sklonuj repozytorium oraz przejdź do katalogu projektu.**
   ```bash
   git clone <adres_repozytorium>
   cd REPHUB
   ```
2. **(Opcjonalnie) utwórz i aktywuj wirtualne środowisko.**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```
3. **Zainstaluj zależności.**
   ```bash
   pip install -r requirements.txt
   ```
   Jeżeli plik `requirements.txt` jest niedostępny, zainstaluj ręcznie `kivy`, `kivymd` oraz
   `pytest`.
4. **Uruchom aplikację.**
   ```bash
   python main.py
   ```
   Pierwsze uruchomienie załaduje przykładową dawkę oraz umożliwi zarządzanie paszami,
   obliczeniami i zapisami.

## Testy i scenariusz końcowy

* Uruchom zestaw testów jednostkowych:
  ```bash
  pytest
  ```
* Uruchom automatyczny tryb testera końcowego bez uruchamiania GUI:
  ```bash
  python - <<'PY'
  from pathlib import Path
  from app.testing import FinalTester

  report = FinalTester(Path('tester_saved.json')).run_walkthrough()
  print('Przygotowano raport testowy z', len(report.saved_state.rows), 'dawkami.')
  PY
  ```
  Wynik pozwala szybko zweryfikować przepływ zapis/edycja/porównanie wraz z ostrzeżeniami.

## Pakietowanie na Windows (opcjonalnie)

Projekt można spakować do pliku `.exe` przy pomocy narzędzia `PyInstaller`:
```bash
pip install pyinstaller
pyinstaller --name RationPlanner --onefile main.py
```

## Znane ograniczenia

* Interfejs użytkownika udostępnia jeden język (PL), ale struktura została przygotowana na
  przyszłą rozbudowę o kolejne tłumaczenia.
* Dane paszowe są przykładowe – w realnym wdrożeniu zaleca się import własnych analiz
  laboratoryjnych.
