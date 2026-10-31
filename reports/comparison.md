# Porównanie retrieval

Status oznaczeń: `human_reviewed`.

Jednostka: różne notatki źródłowe. Obie metody używają identycznego indeksu,
pytań, tokenizacji i filtrów. Dwóch pytań bez danych nie ma w mianowniku.

| Metoda | Trafienia / pytania z odpowiedzią | Hit@5 |
| --- | --- | --- |
| bm25 | 10/10 | 100% |
| overlap | 10/10 | 100% |

| Pytanie | BM25 | Wspólne słowa |
| --- | --- | --- |
| q01 | tak | tak |
| q02 | tak | tak |
| q03 | tak | tak |
| q04 | tak | tak |
| q05 | tak | tak |
| q06 | tak | tak |
| q07 | tak | tak |
| q08 | tak | tak |
| q09 | tak | tak |
| q10 | tak | tak |
| q11 | poza metryką | poza metryką |
| q12 | poza metryką | poza metryką |

## Przypadki nietrafienia

Nie wystąpiło nietrafienie według Hit@5. Ograniczenia ujawniła kontrola
kompletności poniżej: jedno trafne źródło nie wystarcza do porównania prac.

## Kompletność porównań dwóch prac

Hit@5 wystarcza jedno trafne źródło, więc osobno sprawdzono pokrycie prac.

- q08, bm25: dowolne źródło właściwej pracy 1/2, oznaczone trafne źródło 1/2 prac.
  Brakujące prace: `8Wuvhh0LYW`. Ranking skupia wyniki na jednej pracy. Prawdopodobna przyczyna: dopasowanie słów OR bez zapewnienia pokrycia obu nazwanych prac.
- q08, overlap: dowolne źródło właściwej pracy 1/2, oznaczone trafne źródło 1/2 prac.
  Brakujące prace: `8Wuvhh0LYW`. Ranking skupia wyniki na jednej pracy. Prawdopodobna przyczyna: dopasowanie słów OR bez zapewnienia pokrycia obu nazwanych prac.
- q09, bm25: dowolne źródło właściwej pracy 1/2, oznaczone trafne źródło 1/2 prac.
  Brakujące prace: `JAhNsZ9dvG`. Ranking skupia wyniki na jednej pracy. Prawdopodobna przyczyna: dopasowanie słów OR bez zapewnienia pokrycia obu nazwanych prac.
- q09, overlap: dowolne źródło właściwej pracy 1/2, oznaczone trafne źródło 1/2 prac.
  Brakujące prace: `JAhNsZ9dvG`. Ranking skupia wyniki na jednej pracy. Prawdopodobna przyczyna: dopasowanie słów OR bez zapewnienia pokrycia obu nazwanych prac.
- q10, bm25: dowolne źródło właściwej pracy 2/2, oznaczone trafne źródło 2/2 prac.
- q10, overlap: dowolne źródło właściwej pracy 1/2, oznaczone trafne źródło 1/2 prac.
  Brakujące prace: `B9klVS7Ddk`. Ranking skupia wyniki na jednej pracy. Prawdopodobna przyczyna: dopasowanie słów OR bez zapewnienia pokrycia obu nazwanych prac.

## Pytania bez danych

- q11: W zgromadzonym abstrakcie i recenzjach tej pracy nie ma wymaganych pomiarów w podanych jednostkach lub konfiguracji. To nie jest twierdzenie o pełnym PDF-ie.
  bm25: 5 wyników leksykalnych; obecność wyników nie dowodzi wystarczających danych.
  overlap: 5 wyników leksykalnych; obecność wyników nie dowodzi wystarczających danych.
- q12: W zgromadzonym abstrakcie i recenzjach tej pracy nie ma wymaganych pomiarów w podanych jednostkach lub konfiguracji. To nie jest twierdzenie o pełnym PDF-ie.
  bm25: 5 wyników leksykalnych; obecność wyników nie dowodzi wystarczających danych.
  overlap: 5 wyników leksykalnych; obecność wyników nie dowodzi wystarczających danych.

## Interpretacja i ograniczenia

Dziesięć pytań i niepełne oznaczenia nie uzasadniają wniosków o istotności
statystycznej ani o ogólnej przewadze metody. Wynik zależy od słów w pytaniu.
Nazwy metod i słownictwo ze źródeł w pytaniach ułatwiają dopasowanie leksykalne.
Nie dostrajano retrieval po obejrzeniu tego porównania. Powtarzane chunki
jednej recenzji nie są osobnymi trafieniami. Opinie innych recenzentów tej
samej pracy nie zastępują oznaczonych source ID.

Jakość odpowiedzi: **nie oceniano — brak generacji**.
