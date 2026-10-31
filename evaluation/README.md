# Ewaluacja

Zestaw zawiera 10 pytań z odpowiedzią, 2 bez wystarczających danych oraz
19 oznaczeń źródeł. Pliki: [questions.jsonl](questions.jsonl),
[judgments.jsonl](judgments.jsonl), [metadata.json](metadata.json).

## Oznaczenia

Pytanie zawiera unikalny `question_id`, tekst po angielsku, `answerable`
oraz opcjonalne filtry konferencji i typu źródła. Oznaczenie wskazuje
konkretną notatkę przez `source_id`, uzasadnienie i dosłowny fragment dowodowy.
Recenzje tej samej publikacji nie są zamienne. Porównanie dwóch prac
wymaga oznaczeń źródeł obu publikacji.

Dla pytania bez danych zapisane są `absence_reason` i `absence_check`.
Brak wyniku BM25 nie wystarcza do uznania pytania za niemożliwe do rozstrzygnięcia.
Zakres kontroli obejmuje zapisane abstrakty i recenzje, bez pełnych PDF-ów.

## Zamrożenie i uruchomienie

[frozen.json](frozen.json) zapisuje SHA-256 pytań i oznaczeń oraz fingerprint
indeksu. Każda zmiana tych danych wymaga nowej wersji zamrożenia.
Plik istniejącego zamrożenia nie jest nadpisywany.

```bash
.venv/bin/python -m literature_rag evaluate --frozen evaluation/frozen.json --method bm25 --output runs/check-bm25.json
.venv/bin/python -m literature_rag evaluate --frozen evaluation/frozen.json --method overlap --output runs/check-overlap.json
```

Wyniki zapisane z projektem: [porównanie](../reports/comparison.md),
[BM25](../reports/bm25.json) i [baseline](../reports/overlap.json).
Pytania, uzasadnienia i odpowiedzi wzorcowe nie są indeksowane.

## Metryka

`Hit@5 = pytania z przynajmniej jednym trafnym źródłem w top-5 / pytania z odpowiedzią`.

Jednostką jest notatka źródłowa: submission dla abstraktu lub konkretna review.
Kilka fragmentów tej samej recenzji daje jedno źródło. Przy mniej niż pięciu
wynikach oceniane są dostępne; pusty ranking oznacza brak trafienia.
Dwa pytania bez danych nie wchodzą do mianownika.

Obie metody mają 10/10. Mały zestaw i niepełne oznaczenia ograniczają
interpretację tego wyniku. Dla q08 i q09 top-5 nie pokrywa obu porównywanych
prac, mimo trafienia według Hit@5. Przegląd oznaczeń nie był ślepy względem
wyniku wstępnego. Nie dostrajano parametrów po tym porównaniu.

## Generacja

Jakość odpowiedzi: **nie oceniano — brak generacji**. Zachowane są prompty
i konteksty. Gdy generacja jest używana, ocena musi obejmować każde
sprawdzalne twierdzenie, również bez cytowania: `supported`, `unsupported`
lub `contradicted`, z uzasadnieniem względem przywołanego fragmentu.
Poprawny link nie jest sam w sobie dowodem poparcia twierdzenia.

Fixtures w `tests/fixtures/` są fikcyjne i służą wyłącznie sprawdzaniu kodu.
`--allow-synthetic` oznacza wynik jako `synthetic_test_only`.
`--development` służy zestawom roboczym. Jawnie nieprzejrzane oznaczenia
nie mogą być zamrożone jako benchmark końcowy.
