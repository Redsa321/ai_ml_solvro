# Przegląd literatury — OpenReview

Lokalny program CLI do wyszukiwania publikacji i oficjalnych recenzji
ICLR 2024 oraz NeurIPS 2024 dotyczących efektywności inferencji LLM.
Realizacja [zadanie.md](zadanie.md), w dopuszczalnym wariancie bez generacji LLM.

Próba do oddania obejmuje **36 prac i 142 oficjalne recenzje**:
16 prac ICLR i 20 NeurIPS. Rozmiar próby wynika z ograniczeń dostępu
do publicznych recenzji OpenReview. Zachowano pierwotny cel 30 + 30,
brakujące ID i uzasadnienie w [doborze próby](data/curation/submission-selection.json).

Python 3.12+ z SQLite FTS5; brak zależności uruchomieniowych.
Sprawdzone na Pythonie 3.14.8. Komendy wykonuj z głównego folderu projektu.
Praca na zapisanym korpusie nie wymaga konta OpenReview ani klucza API.

## Uruchomienie

Archiwum do oddania zawiera kod, dane, bazę, manifesty, benchmark i przykłady.
Instrukcja dla oceniającego: [ODDANIE.md](ODDANIE.md).
Same pliki Git nie zawierają ignorowanych snapshotów i baz.

W świeżym folderze utwórz środowisko; w obecnym projekcie `.venv` już istnieje:

```bash
python3 -m venv --without-pip .venv
.venv/bin/python -m literature_rag --help
.venv/bin/python -m literature_rag search "KV cache memory reduction"
```

Nie trzeba aktywować środowiska. Opcjonalnie w fish:
`source .venv/bin/activate.fish`, a w Bash: `source .venv/bin/activate`.
Po aktywacji można zastąpić `.venv/bin/python` przez `python`.

**Domyślna baza to prawdziwe dane w `data/index/real.sqlite`.**
Fikcyjne demo korzysta z osobnej `data/index/demo.sqlite`.

## Wyszukiwanie i filtry

Pytania wpisuj po angielsku. Wyszukiwanie leksykalne nie tłumaczy zapytań.

```bash
.venv/bin/python -m literature_rag search "quantization outliers low-bit limitations" --kind official_review
.venv/bin/python -m literature_rag search "KV cache long context memory" --conference neurips2024
.venv/bin/python -m literature_rag search "speculative decoding latency" --method overlap --top-k 10
```

| Opcja | Działanie |
| --- | --- |
| `--conference iclr2024` / `neurips2024` | Filtr konferencji przed top-k |
| `--kind author_abstract` / `official_review` | Abstrakty autorów lub konkretne recenzje |
| `--method bm25` / `overlap` | BM25 (domyślne) lub liczba wspólnych słów |
| `--top-k 5` | Maksymalna liczba różnych źródeł, nie chunków |
| `--json` | Pełny wynik wyszukiwania w JSON |
| `--db plik.sqlite` | Jawny wybór innej bazy |

Wynik zawiera fragment, nazwę pola, rodzaj źródła i bezpośredni link OpenReview.
Score nie jest prawdopodobieństwem trafności. Przy braku wyników CLI informuje
o braku dopasowania, co samo nie dowodzi braku odpowiedzi w całym korpusie.

## Prompt, dokładny kontekst i źródła

```bash
.venv/bin/python -m literature_rag ask "Compare OmniQuant and QLLM quantization limitations" --provider none
```

Komenda wypisuje katalog `runs/ask-.../`, zawierający:

- `prompt.txt` — dokładny końcowy prompt;
- `context.json` — fragmenty po ograniczeniu objętości;
- `sources.json` — etykiety cytowań, note ID, publikacje, pola, zakresy i linki;
- `retrieval.json` — ranking, filtry i score;
- `metadata.json` — fingerprint danych, indeksu i status generacji.

`--provider none` zapisuje `generation_status=not_run`, bez odpowiedzi modelu.
Do recenzji może zostać dołączony abstrakt właściwej pracy; ma
`origin=added_by_relation` i nie zwiększa Hit@5. Prompt rozdziela deklaracje
autorów i opinie recenzentów, wymaga cytowań oraz zaznaczania braków.
Domyślny limit tekstu kontekstu to 12 000 znaków (`--max-chars`).

## Dane i odtwarzanie offline

Domyślny indeks zawiera 36 prac, 178 źródeł i 921 fragmentów.
Relacje publikacja–recenzja oraz oryginalne pola ocen są zachowane.
Komentarze, decyzje, rebuttale i metarecenzje pozostają w raw poza indeksem.
SQLite + FTS5 wybrano ze względu na mały korpus, pracę na CPU i prostą odbudowę;
embeddingi i osobny serwer nie są wymagane.

```bash
.venv/bin/python -m literature_rag build --manifest data/manifests/corpus.json
.venv/bin/python -m literature_rag doctor
```

Powtórny import jest idempotentny. Import innych danych do istniejącego indeksu
wymaga osobnego `--db` albo jawnego `--replace`. Manifest sprawdza SHA-256 raw
pliku i fingerprint korpusu; trzeba zachować go razem ze snapshotem.
Szczegóły: [format snapshotu](docs/SNAPSHOT_FORMAT.md).

Pobieranie danych realizuje [eksporter API w przeglądarce](docs/BROWSER_EXPORT.md).
Python nadal otrzymuje `403 ChallengeRequiredError`; nie omijamy weryfikacji.
Historyczne formularze pobierane są z `expired=true`. Pełny pierwszy eksport
60 prac zachowano jako materiał audytu; nie jest końcową próbą tematyczną.

## Ewaluacja

Zestaw w `evaluation/` zawiera 10 pytań z odpowiedzią, 2 bez danych
i 19 sprawdzonych oznaczeń źródeł z cytatami i uzasadnieniem.
Metadane opisuje [evaluation/metadata.json](evaluation/metadata.json).
Pytania, uzasadnienia i oznaczenia nie trafiają do indeksu.

| Metoda | Trafienia / pytania z odpowiedzią | Hit@5 |
| --- | --- | --- |
| BM25 | 10/10 | 100% |
| Wspólne słowa | 10/10 | 100% |

To wynik małej próby, względem niepełnych oznaczeń. **Nie oznacza kompletności
odpowiedzi:** w q08 i q09 obie metody odnalazły źródła tylko jednej z dwóch
porównywanych prac. Raport pokazuje te porażki i oba pytania bez danych.
Nie dostrajano wyszukiwania po obejrzeniu wyników. Poparcia wygenerowanych
twierdzeń nie oceniano — nie uruchomiono generacji.

```bash
.venv/bin/python -m literature_rag evaluate --frozen evaluation/frozen.json --method bm25 --output runs/evaluation-bm25.json
.venv/bin/python -m literature_rag evaluate --frozen evaluation/frozen.json --method overlap --output runs/evaluation-overlap.json
```

Zmiana pytań, oznaczeń lub indeksu po zamrożeniu powoduje błąd.
Propozycje oznaczone `human_reviewed=false` można zamrozić wyłącznie jako
`--development`, nie jako benchmark końcowy.
Protokół: [evaluation/README.md](evaluation/README.md).

## Pakiet do oddania

```bash
.venv/bin/python scripts/package_submission.py --output dist/literature-rag-submission.tar.gz
.venv/bin/python scripts/verify_submission.py dist/literature-rag-submission.tar.gz
```

Pakowanie dobiera dane z [reports/submission.json](reports/submission.json).
Nie dołącza `.env`, `.git`, `.venv`, cache ani niepowiązanych uruchomień.
`BUNDLE.json` zawiera listę plików, rozmiary i SHA-256. Istniejącego archiwum
nie nadpisuje: dla kolejnej wersji wskaż nową nazwę.
Weryfikator rozpakowuje do świeżego katalogu, usuwa dołączoną bazę, odbudowuje
ją ze snapshotu, odtwarza oba rankingi i zapisuje nowy prompt bez API.

## Opcjonalne Gemini

Adapter REST istnieje i ma testy na atrapach. Po potwierdzeniu bezpłatnego
dostępu przygotuj lokalny `.env` według `.env.example`, ustawiając
`GEMINI_API_KEY` i dostępną nazwę `GEMINI_MODEL`. Plik `.env` jest ignorowany przez Git.
Zmienne środowiskowe mają pierwszeństwo nad `.env`.

```bash
.venv/bin/python -m literature_rag ask "Which inference limitations do reviewers identify?" --provider gemini
```

Odpowiedź zapisuje się jako `answer.md`. Prompt i kontekst powstają przed
wywołaniem API. Pusty kontekst nie uruchamia modelu; błąd zachowuje prompt.
Nieznane etykiety cytowań dają `invalid_citations`; samo poprawne ID nie dowodzi
poparcia twierdzenia. Nie ma automatycznego płatnego fallbacku.
Generacja pozostaje opcjonalna i nie jest częścią przedstawionych wyników.

## Sprawdzenie kodu i demo

```bash
.venv/bin/python -W error::ResourceWarning -m unittest discover -s tests -v
.venv/bin/python -m compileall -q literature_rag scripts tests
node --test tests/test_exporter.cjs
.venv/bin/python -m literature_rag demo
```

Testy są offline; Node służy testom eksportera. Demo to jawnie fikcyjne
3 publikacje i 4 recenzje z linkami `example.invalid`, zapisane w osobnej bazie.
Nie nadpisuje domyślnego indeksu prawdziwych danych i nie mierzy jakości badań.

## Dokumentacja projektu

- [Raport końcowy](reports/raport.md) i [porównanie per pytanie](reports/comparison.md).
- [Architektura](docs/ARCHITECTURE.md) — przepływ danych i decyzje techniczne.
- [Audyt tematu](reports/topic-audit.md), [audyt korpusu](reports/corpus-audit.json)
  i [oryginalne skale ocen](reports/rating-scales.json).
