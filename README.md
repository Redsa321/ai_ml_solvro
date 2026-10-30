[# Asystent przeglądu literatury — OpenReview

Projekt na podstawie [zadanie.md](zadanie.md): publikacje i oficjalne recenzje
ICLR 2024 oraz NeurIPS 2024 dotyczące efektywności inferencji LLM.

Zaimplementowano działający rdzeń offline: import lokalnego snapshotu,
SQLite/FTS5, BM25, baseline wspólnych słów, kontekst i prompty z cytowaniami,
zamrażanie oznaczeń oraz ewaluację Hit@5. Prawdziwe dane OpenReview są już
lokalnie: pełny pierwszy eksport zawiera 60 prac i 235 oficjalnych recenzji.
Po przeglądzie tematu dostępna próba obejmuje 36 prac i 142 recenzje.
Do skompletowania docelowych 30 + 30 prac pozostają recenzje dla 24 wybranych ID.

Program wymaga Python 3.12+ z SQLite FTS5. Nie ma zależności uruchomieniowych.
Komendy poniżej wykonuj z głównego folderu projektu. Działa też zwykłe
`python3 -m literature_rag ...`; instalacja pakietu nie jest konieczna.

## Praca offline na prawdziwych danych

Te komendy działają teraz, bez internetu i bez klucza LLM:

```bash
.venv/bin/python -m literature_rag doctor --db data/index/topic-reviewed-partial.sqlite
.venv/bin/python -m literature_rag search "quantization outliers low-bit limitations" --db data/index/topic-reviewed-partial.sqlite --kind official_review
.venv/bin/python -m literature_rag search "KV cache long context memory" --db data/index/topic-reviewed-partial.sqlite --conference neurips2024 --method overlap
.venv/bin/python -m literature_rag ask "Compare OmniQuant and QLLM quantization limitations" --db data/index/topic-reviewed-partial.sqlite --provider none
```

W `data/index/collected.sqlite` jest pełny pierwszy eksport: 60 prac,
295 źródeł i 1533 fragmenty. W `data/index/topic-reviewed-partial.sqlite`
jest próba po przeglądzie tematu: 36 prac, 178 źródeł i 921 fragmentów.
Obejmuje 16 prac ICLR oraz 20 NeurIPS. Oryginalny eksport pozostaje zachowany.
Domyślna baza `data/index/corpus.sqlite` nadal służy fikcyjnemu demo;
dla prawdziwych danych podawaj jawnie `--db`, jak powyżej.

Raport roboczy: [reports/raport.md](reports/raport.md).
Decyzje doboru: [reports/topic-audit.md](reports/topic-audit.md).
Sprawdzenie importu, odbudowy offline i pakietów promptów:
[reports/data-validation.json](reports/data-validation.json).

Po odzyskaniu internetu można uzupełnić brakujące prace według ustalonej listy.
Przygotowanie skryptu jest lokalne:

```bash
.venv/bin/python scripts/prepare_browser_export.py --selection data/curation/topic-selection.json
```

Wczytaj wygenerowany `runs/export-topic-reviewed.js` w konsoli zalogowanej
strony `openreview.net`, zgodnie z [instrukcją eksportu](docs/BROWSER_EXPORT.md).
Zapisze `openreview-topic-reviewed.json`. Będzie korzystać z cache tej samej
karty; po zamknięciu karty dane trzeba pobrać ponownie. Przy braku sieci
można dalej używać obu lokalnych baz.

## Szybki start bez OpenReview i bez kluczy

```bash
python3 -m venv --without-pip .venv
.venv/bin/python -m literature_rag doctor
.venv/bin/python -m literature_rag demo
.venv/bin/python -m literature_rag search "quantization quality limitations" --kind official_review
.venv/bin/python -m literature_rag search "KV cache compression" --conference neurips2024 --method overlap
.venv/bin/python -m literature_rag ask "What limitations do reviewers identify in quantization?" --provider none
```

**Demo wykorzystuje fikcyjne dane:** 3 publikacje, 4 recenzje, komentarz,
decyzję i rebuttal. Tytuły są oznaczone `[FICTIONAL]`, a linki prowadzą do
`example.invalid`. To sprawdzenie działania kodu, nie korpus badawczy ani
wynik jakości systemu. Komentarze, decyzje i rebuttale nie trafiają do indeksu.

`demo` tworzy `data/index/corpus.sqlite`, manifest w `data/manifests/`
i pakiet w `runs/ask-.../`. Kolejne uruchomienie użyje tego samego indeksu,
jeśli dane i konfiguracja się nie zmieniły. Innego indeksu nie nadpisze bez
jawnego `--replace`; można zawsze wskazać osobny `--db`.

## Zapis odpowiedzi bez modelu

`ask --provider none` zapisuje przed jakimkolwiek wywołaniem modelu:

- `retrieval.json` — ranking różnych źródeł, filtry, score i tokeny zapytania;
- `context.json` — dokładne fragmenty po ograniczeniu objętości;
- `sources.json` — mapowanie etykiet na note ID, chunk, publikację, pole i URL;
- `prompt.txt` — końcowy tekst do przekazania modelowi;
- `metadata.json` — fingerprint korpusu i indeksu oraz status generacji.

Brak `answer.md` i `generation_status=not_run` oznaczają brak generacji.
Prompt zawiera osobne role autora i recenzenta, zasady cytowania i odmowy
przy braku podstaw. Do odnalezionej recenzji może zostać dołączony abstrakt
tej samej pracy; ma `origin=added_by_relation` i nie zwiększa Hit@5.

Wyszukiwanie działa leksykalnie po angielsku, bez embeddingów i tłumaczenia.
Hit@5 dotyczy różnych źródeł, a nie chunków. Typy źródeł można ograniczać
przez `--kind author_abstract` lub `--kind official_review`. `--json` w komendzie
`search` daje pełny wynik do dalszego przetwarzania. Filtr konferencji przyjmuje
aliasy `iclr2024`/`neurips2024` lub pełne identyfikatory.

## Import i odtwarzanie danych

Format lokalnego eksportu i weryfikację invitations opisuje
[docs/SNAPSHOT_FORMAT.md](docs/SNAPSHOT_FORMAT.md). Wystarczy przygotować
snapshot z notatkami pobranymi oficjalną metodą; importer nie potrzebuje konta.

Jeśli zalogowana przeglądarka czyta API, a Python nadal otrzymuje 403, użyj
[eksportera przeglądarkowego](docs/BROWSER_EXPORT.md). Skrypt
[scripts/export-openreview.js](scripts/export-openreview.js) pobiera po
30 prac z obu konferencji i zapisuje lokalny JSON wraz z publicznymi
recenzjami, rzeczywistymi schematami i historią wyboru próby.
Uruchamia się go w konsoli strony konferencji w `https://openreview.net/`;
sesja pozostaje w przeglądarce. Firefox JSON Viewer w domenie API blokuje fetch,
dlatego eksporter odrzuca ten kontekst przed rozpoczęciem pobierania.
Historyczne schematy recenzji pobiera z `expired=true`, zachowując oryginalne
skale, w tym formaty `3 good` i `6: ...`.
Nie ma jeszcze bezpośredniego klienta Python ani komendy `fetch`.

```bash
.venv/bin/python -m literature_rag build --snapshot data/raw/my-snapshot.json --db data/index/real.sqlite
.venv/bin/python -m literature_rag search "KV cache memory" --db data/index/real.sqlite
```

Indeks da się odtworzyć offline z wygenerowanego manifestu. Przekaż jego
rzeczywistą ścieżkę do `build --manifest ... --db data/index/rebuilt.sqlite`.
Manifest sprawdza hash snapshotu i zapisuje konfigurację chunkingu oraz wybrane ID.
Raw JSON i manifest trzeba zachować razem; manifest nie zawiera pełnej treści źródeł.

## Ewaluacja

Po przygotowaniu prawdziwego korpusu ręcznie oznacz źródła i uzasadnienia,
stosując [evaluation/README.md](evaluation/README.md). Następnie:

```bash
.venv/bin/python -m literature_rag freeze --db data/index/real.sqlite --questions evaluation/questions.jsonl --judgments evaluation/judgments.jsonl
.venv/bin/python -m literature_rag evaluate --db data/index/real.sqlite --frozen evaluation/frozen.json --method bm25
.venv/bin/python -m literature_rag evaluate --db data/index/real.sqlite --frozen evaluation/frozen.json --method overlap
```

Każde uruchomienie zapisuje oddzielny `runs/eval-.../results.json`: wynik
per pytanie, licznik i mianownik Hit@5 oraz ograniczenia. Zmiana pytań,
oznaczeń lub konfiguracji indeksu po zamrożeniu powoduje błąd.
Końcowy benchmark wymaga minimum 10 pytań z odpowiedzią i 2 bez danych;
`freeze --development` pozwala utworzyć mniejszy zestaw roboczy.

Przykładowe pliki w `tests/fixtures/` służą wyłącznie testom. Aby sprawdzić
na nich narzędzia, użyj `freeze` i `evaluate` z `--allow-synthetic` oraz osobnym
plikiem zamrożenia. Wynik zostanie oznaczony `synthetic_test_only`.
Nie przygotowano jeszcze benchmarku ani raportu jakości na rzeczywistych pracach.

Jest gotowy [szkic do weryfikacji](evaluation/draft/review.md): 12 pytań
i 19 oznaczeń z cytatami. Powstał na dostępnych 36 pracach; metadane wyraźnie
oznaczają autora jako asystenta i `human_reviewed=false`. Nie został zamrożony
ani użyty do końcowego porównania. Po uzupełnieniu korpusu trzeba sprawdzić
oznaczenia i brak danych oraz przeprowadzić przegląd przez człowieka.

## Opcjonalne Gemini API

Adapter REST jest zaimplementowany i sprawdzony na atrapach transportu.
Nie wykonano rzeczywistych wywołań modelu. Po potwierdzeniu bezpłatnego dostępu
skopiuj `.env.example` do lokalnego `.env` i wpisz klucz oraz dostępną nazwę modelu.
Zmienne środowiskowe mają pierwszeństwo nad `.env`. Obsługiwane są pojedyncze
wiersze `NAZWA=wartość`, opcjonalnie z prostymi cudzysłowami, bez interpolacji.

```bash
.venv/bin/python -m literature_rag ask "Which inference limitations are identified?" --db data/index/real.sqlite --provider gemini
```

Domyślny provider to `none`, chyba że świadomie ustawisz `GENERATION_PROVIDER=gemini`.
Model nie ma dostępu do web search ani innych narzędzi. Przy pustym kontekście
nie jest wywoływany. Błąd dostępu zachowuje prompt; nie ma zmiany dostawcy ani
automatycznego płatnego fallbacku. Sam klucz nie potwierdza darmowego planu —
sprawdź projekt w AI Studio przed uruchomieniem. Limit tekstu kontekstu to
domyślnie 12 000 znaków, wyjścia 1536 tokenów; nie jest to dokładny licznik
tokenów wejścia dla dowolnego modelu. Wywołanie może zgłosić limit dostawcy.

Odpowiedź trafia do `answer.md`. Nieznane etykiety cytowań pozostają w surowej
odpowiedzi i dają status `invalid_citations`; poprawne etykiety nadal wymagają
ręcznej oceny poparcia twierdzeń. Dokumentacja adaptera:
[Gemini generateContent](https://ai.google.dev/api/generate-content).

## Weryfikacja kodu

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall -q literature_rag tests
node --test tests/test_exporter.cjs
```

Testy nie wymagają sieci, kont OpenReview ani kluczy API. Node jest opcjonalny
i służy testom eksportera oraz jego zgodności z importerem. Obejmują klasyfikację
źródeł, błędne przypisania, idempotencję i odbudowę indeksu, atomowy zapis,
filtry i deduplikację, pochodzenie cytowań, brak generacji, atrapy Gemini,
zamrożenie benchmarku, metrykę i pełną ścieżkę CLI. Narzędzie `ruff` jest
skonfigurowane w `pyproject.toml`, ale nie jest wymagane do uruchomienia;
nie było dostępne w początkowym środowisku.

Inwentarz oryginalnych skal ocen można odtworzyć z lokalnych raw invitations:

```bash
.venv/bin/python -m literature_rag.schema --snapshot data/raw/openreview-v3-830dc090e225.json --output reports/rating-scales.json
```

Obsługuje tekstowe enumy ICLR oraz obiekty enumów NeurIPS z polem `value`.
Nie przeskalowuje ocen zapisanych przy recenzjach.

## Plan i instrukcje projektu

- [PLAN.md](PLAN.md) — analiza wymagań, architektura, harmonogram,
  kryteria ukończenia, ryzyka dostępu i protokół ewaluacji.
- [AGENTS.md](AGENTS.md) — wspólne reguły pracy agentów w tym folderze.
- [openreview-corpus](.agents/skills/openreview-corpus/SKILL.md) — pozyskanie i odtwarzanie danych.
- [rag-evidence](.agents/skills/rag-evidence/SKILL.md) — retrieval, kontekst i cytowania.
- [rag-evaluation](.agents/skills/rag-evaluation/SKILL.md) — oznaczenia, metryki i raport.

Skille są lokalne w `.agents/skills/`, zgodnie z
[dokumentacją Codex](https://learn.chatgpt.com/docs/build-skills).
Można wywołać je jawnie jako `$openreview-corpus`, `$rag-evidence`
i `$rag-evaluation`. Jeśli klient ich nie wykryje, uruchom ponownie sesję
w tym folderze. `AGENTS.md` zawiera również bezpośrednie odnośniki do instrukcji.

Klucze pozostają w ignorowanym `.env` lub zmiennych środowiskowych. Pobrane
snapshoty, bazy i pełne runs są lokalnymi artefaktami. Na oddanie trzeba
przygotować pakiet prawdziwych danych do odtworzenia offline. Fixtures są
oddzielnymi danymi testowymi; dostępne prawdziwe snapshoty znajdują się w `data/raw/`.
