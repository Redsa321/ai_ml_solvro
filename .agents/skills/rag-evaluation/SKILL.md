---
name: rag-evaluation
description: Przygotuj i przeprowadź uczciwą ewaluację wyszukiwania i odpowiedzi asystenta OpenReview w tym projekcie. Używaj do pytań, ręcznych oznaczeń źródeł, Hit@5, porównania z baseline i raportowania błędów; nie do zwykłej implementacji retrieval bez oceny eksperymentalnej.
---

# Ewaluacja RAG

Odczytaj protokół i etap E4 oraz E7 w [PLAN.md](../../../PLAN.md).
Nie wyprowadzaj trafności wyłącznie ze zgodności tytułu lub z rankingu badanej metody.

## Przygotowanie przed końcowym porównaniem

- Na podstawie lektury lokalnych źródeł przygotuj 10 pytań z odpowiedzią
  i 2 bez wystarczających danych. Obejmij autorów, recenzentów, ograniczenia,
  porównanie dwóch prac i filtr konferencji, jeśli korpus to umożliwia.
- Dla każdego pytania z odpowiedzią ręcznie wskaż co najmniej jeden konkretny
  `source_id`, uzasadnienie i fragment potwierdzający trafność. Pytanie o
  porównanie dwóch prac wymaga oznaczeń dla obu; Hit@5 sam nie mierzy kompletności.
- Dla pytań bez danych zapisz rodzaj braku i jak go sprawdzono w korpusie.
  Brak znalezionego wyniku to za mało do ustanowienia ground truth.
- Sprawdź istnienie ID i zgodność z filtrem konferencji. Zamroź pytania,
  oznaczenia i fingerprint korpusu przed finalnym uruchomieniem metod.
  Użyj osobnych pytań roboczych do ustalania parametrów.
- Nie indeksuj pytań, uzasadnień i odpowiedzi wzorcowych. Zmiana zamrożonych
  oznaczeń po wykryciu rzeczywistego błędu wymaga nowej wersji, opisania
  powodu i ponownego uruchomienia obu metod; nie jest niewidoczną poprawką.

## Retrieval

- Uruchom BM25 i wspólne słowa na identycznym korpusie, chunkach, pytaniach,
  query preprocessing i filtrach. Przy opcjonalnym tłumaczeniu obie metody
  dostają ten sam zapisany tekst tłumaczenia.
- Jednostką oceny jest dokument źródłowy: abstrakt submission lub review note.
  Zredukuj ranking chunków do różnych `source_id`, zachowując najlepszy chunk.
  Nie utożsamiaj wszystkich recenzji tej samej pracy.
- Oblicz `Hit@5 = liczba_pytań_z_trafieniem / liczba_pytań_z_odpowiedzią`.
  Trafienie oznacza przecięcie top-5 różnych ID z ręcznymi oznaczeniami.
  Przy mniej niż pięciu wynikach oceniaj dostępne. Pusty ranking daje zero.
- Oddaj ranking, score, filtry, trafienie i czas dla każdego pytania oraz
  wynik zbiorczy z licznikiem i mianownikiem. Zapytania bez danych raportuj osobno.
- Przy niepełnych oznaczeniach nie raportuj Recall@k jako miary kompletności.
  Przy dziesięciu pytaniach nie ogłaszaj istotności statystycznej niewielkiej różnicy.

## Generacja i raport

- Weryfikuj wyłącznie faktycznie wygenerowane i zapisane odpowiedzi. Pracuj
  na dokładnie tym kontekście, który dostał model, nie na później poszerzonym zbiorze.
- Rozbij odpowiedź na sprawdzalne twierdzenia. Zapisz treść twierdzenia,
  etykiety cytowań, ocenę poparcia i krótkie uzasadnienie. Mianownik obejmuje
  także sprawdzalne twierdzenia bez cytowania; sprzeczność i brak poparcia
  nie są trafieniami. `supported` wymaga poparcia właśnie w przywołanym
  fragmencie; istnienie poparcia gdzie indziej w kontekście nie wystarcza.
  Oddziel wypowiedzi nieweryfikowalne i abstencję.
- Raportuj wspierane/przeglądane twierdzenia z licznikiem i mianownikiem.
  Przy zerowym mianowniku podaj „nie dotyczy”, nie 100%. Odnotuj odpowiedzi,
  które nie odpowiedziały na pytanie mimo dostępnych danych.
- Osobno opisz oba pytania bez danych: odmowę, częściową odpowiedź albo
  nieuzasadnione twierdzenia. Samo podobieństwo leksykalne nie potwierdza podstaw.
- Bez LLM zapisz „nie oceniano — brak generacji”. Wyniki ręcznego przeniesienia
  promptu do ChatGPT/Gemini, jeśli użytkownik je wykona, są osobnym trybem
  manualnym, nie generacją działającej aplikacji CLI.
- Opisz co najmniej jedną rzeczywistą porażkę i prawdopodobną przyczynę,
  różnice między metodami, bias próby i ograniczenia oznaczeń. Wnioski muszą
  wynikać z artefaktów; nie dopisuj brakujących wyników ani fikcyjnych przykładów.

Zweryfikuj metrykę na ręcznie policzalnym przykładzie: powtarzane chunki
tej samej recenzji, trafna recenzja dopiero po deduplikacji, pusty ranking
oraz wyłączenie pytań bez danych z mianownika. Testuj definicję, nie docelowy wynik.
