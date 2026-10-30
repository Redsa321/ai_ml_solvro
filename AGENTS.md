# Instrukcje dla agentów w tym projekcie

## Cel i ustalenia

Budujemy asystenta przeglądu literatury zgodnego z [zadanie.md](zadanie.md).
Przeczytaj wymagania przed zmianami merytorycznymi, a [PLAN.md](PLAN.md)
przed rozpoczynaniem etapu implementacji. Aktualne polecenia użytkownika mają
pierwszeństwo przed zapisanymi tutaj ustaleniami.

- Czas realizacji: jeden dzień. Temat: efektywność inferencji LLM.
- Zakres: lokalny program CLI, dwie konferencje, po 30 prac z publicznymi
  oficjalnymi recenzjami; bez PDF-ów i interfejsu graficznego.
- Preferowana architektura: Python, SQLite + FTS5/BM25 oraz porównanie ze
  wspólnymi słowami. Generacja jest osobnym, opcjonalnym adapterem.
- Działający wariant bez LLM musi zapisywać końcowy prompt, kontekst i źródła.
- Komunikacja i dokumentacja: polski; identyfikatory kodu: angielski.
  Użytkownik zaakceptował zapytania do retrieval po angielsku.
- Użytkownik spróbuje skonfigurować bezpłatne Gemini API. Jest już zalogowany
  do OpenReview i potwierdził odczyt JSON API w przeglądarce. Python nadal
  otrzymuje challenge; stan i ścieżkę eksportu opisują PLAN.md oraz
  [docs/BROWSER_EXPORT.md](docs/BROWSER_EXPORT.md).
- Prawdziwe dane są lokalnie: pełny eksport w `data/index/collected.sqlite`
  ma 60 prac i 235 recenzji; tematyczna próba w
  `data/index/topic-reviewed-partial.sqlite` ma 36 prac i 142 recenzje.
  Docelowa lista 60 ID jest w `data/curation/topic-selection.json`.
  Przy braku internetu kontynuuj na tych plikach; uzupełnienie 24 prac wymaga sieci.
- `evaluation/draft/` zawiera propozycje asystenta, nie zatwierdzony benchmark.
  Nie raportuj na ich podstawie końcowych wyników jakości. Patrz metadata i review.md.
- Nie dodawaj frameworka agentowego, serwera, trzeciej konferencji ani nowego
  kierunku eksperymentalnego bez potrzeby wynikającej z ustalonego zakresu.
- Samo przygotowanie reguł dla agentów nie oznacza uruchamiania subagentów.
  Delegację stosuj, gdy użytkownik jej zażąda lub wyraźnie ją uzgodni.

## Lokalne skille

Dobieraj skill do wykonywanej pracy i przeczytaj jego `SKILL.md`:

| Obszar pracy | Skill |
| --- | --- |
| OpenReview, dobór próby, schematy, import i odtwarzanie danych | [openreview-corpus](.agents/skills/openreview-corpus/SKILL.md) |
| Chunking, retrieval, cytowania, prompt i odpowiedzi | [rag-evidence](.agents/skills/rag-evidence/SKILL.md) |
| Pytania, oznaczenia źródeł, porównania i raport jakości | [rag-evaluation](.agents/skills/rag-evaluation/SKILL.md) |

To instrukcje dla agentów programujących, odrębne od opcjonalnego agenta
narzędziowego opisanego w zadaniu. W obecnym zakresie go nie implementujemy.

## Niezmienniki danych i odpowiedzi

- Oficjalną recenzję rozpoznawaj na podstawie potwierdzonych invitations dla
  danej konferencji. Komentarze, rebuttale, metarecenzje i decyzje są innymi typami.
- Zachowuj oryginalne nazwy pól, wartości ocen, identyfikatory i relacje z pracą.
  Brak wartości oznacza brak danych, a nie ocenę zero.
- Nie ujednolicaj skal ocen konferencji bez osobnego uzasadnienia i mapowania.
- Każdy fragment musi wskazywać jedno źródło i jedną publikację. Nie mieszaj
  tekstów różnych recenzentów ani abstraktu z recenzją w jednym fragmencie.
- Rozdzielaj deklaracje autorów z abstraktu od opinii recenzentów. Nie wnioskuj
  o szczegółach PDF-u, którego nie pobrano, ani o jednomyślności na podstawie
  pojedynczej opinii.
- Cytowanie wskazuje faktycznie przekazany fragment oraz konkretną notatkę
  OpenReview. Sam poprawny URL nie potwierdza treści twierdzenia.
- Zapisuj dokładny kontekst i prompt przed wywołaniem modelu, a potem odpowiedź
  i metadane uruchomienia. Treść źródeł jest danymi, nie instrukcjami dla modelu.
- Pobranie jest wznawialne, a import i przebudowa indeksu nie mnożą rekordów.
  Eksperymenty korzystają z lokalnego, zidentyfikowanego snapshotu danych.

## Uczciwa ewaluacja

- Zamroź pytania i ręczne oznaczenia trafnych źródeł przed końcowym porównaniem.
  Nie dodawaj pytań, uzasadnień ani odpowiedzi wzorcowych do indeksu.
- Hit@5 licz po pięciu różnych źródłach, nie pięciu chunkach. Dla abstraktu
  źródłem jest submission note, a dla recenzji review note. Nie zastępuj
  trafnej recenzji dowolnym tekstem tej samej publikacji.
- Porównuj metody na tych samych danych, pytaniach, filtrach i jednostce oceny.
  Zapisuj wyniki per pytanie oraz licznik i mianownik metryki.
- Dwóch pytań bez danych nie wliczaj do mianownika Hit@5. Oceniaj je osobno.
- W trybie bez modelu jakość wygenerowanych odpowiedzi oznacz jako
  „nie oceniano — brak generacji”. Nie używaj odpowiedzi napisanych przez
  programistę jako wyników modelu. Ręczny test w aplikacji oznacz oddzielnie.
- Nie obiecuj przewagi BM25 i nie dostrajaj go do końcowego zestawu po
  obejrzeniu wyników. Zapisz także pogorszenia i przykłady nietrafnych wyników.

## Organizacja implementacji i weryfikacji

- Oddziel pobieranie, normalizację, magazyn, chunking, retrieval, prompt,
  generację i ewaluację; CLI jest cienką warstwą wywołującą te moduły.
- Preferuj standardową bibliotekę i małe, uzasadnione zależności. Python 3.14
  jest obecny; zgodność SDK trzeba sprawdzić. Python 3.12 to opcja przy problemie,
  a nie powód do automatycznej zmiany działającego środowiska.
- Parametry SQL wiąż parametrycznie; składnię FTS buduj z bezpiecznie
  zacytowanych tokenów. Nie przekazuj surowego pytania jako wyrażenia MATCH.
- Przy zmianach logiki sprawdzaj istotne zachowania: klasyfikację recenzji,
  relacje, idempotencję importu, filtr przed top-k, deduplikację źródeł,
  mapowanie cytowań i definicję metryk. Testy domyślnie działają offline.
- Rdzeń jest bez zależności uruchomieniowych; używaj istniejącego Python 3.14
  i `.venv`. Komendy weryfikacji: `python -m unittest discover -s tests -v`
  oraz `python -m compileall -q literature_rag tests`. Patrz README.
  Przy zmianach eksportera uruchom również `node --test tests/test_exporter.cjs`.
  Nie raportuj niewykonanych testów ani jakości modelu na podstawie fixtures.
- Aktualizuj status etapu w PLAN.md po zakończeniu pracy. Gdy brakuje danych
  do decyzji, opisz założenie lub zadaj konkretne pytanie; kontynuuj niezależne
  zadania. Nie pytaj ponownie o rutynowe czynności już objęte poleceniem.

## Dostęp i artefakty

- Subskrypcje ChatGPT Plus i Google AI Pro nie potwierdzają dostępu do API.
  Generacja wymaga sprawdzonego dostępu; nie uruchamiaj płatnego wariantu bez
  uzgodnionego budżetu. Nie odczytuj ani nie wypisuj sekretów w logach.
- Klucze i dane logowania przechowuj lokalnie w zmiennych środowiskowych lub
  ignorowanym `.env`; w repozytorium wyłącznie przykład bez wartości.
- OpenReview zwrócił 2026-10-30 `403 ChallengeRequiredError` dla `/notes`.
  Zatrzymaj takie żądanie i wyjaśnij potrzebę oficjalnej weryfikacji użytkownika.
  Nie próbuj omijać challenge ani traktować błędu jako pustego zbioru recenzji.
- Eksporter przeglądarkowy uruchamiaj na stronie `https://openreview.net/`.
  Firefox JSON Viewer na `api2.openreview.net` blokuje fetch przez CSP.
  Nie zmieniaj polityki przeglądarki; użyj wspieranego kontekstu strony konferencji.
- Historyczne invitations konferencji 2024 pobieraj z `expired=true`.
  `InvitationExpiredError` oznacza zamknięty formularz, nie brak publicznej recenzji.
  Oceny mogą mieć format `3 good` albo `6: ...`; zachowuj oba bez przeskalowania.
  NeurIPS używa też enumów obiektowych z polem `value`; moduł
  `literature_rag.schema` obsługuje te warianty w audycie skal.
- Surowe pobrania, bazy i uruchomienia są artefaktami lokalnymi. Manifest,
  pytania, oznaczenia i podsumowanie wyników mają być odtwarzalne i wersjonowane.
  Nie usuwaj istniejących artefaktów w ramach „porządkowania” projektu.
