# Przegląd literatury OpenReview — raport końcowy

Stan na 2026-10-31. Program CLI działa offline na rzeczywistych danych.
Oddawany wariant nie generuje odpowiedzi LLM; zapisuje końcowy prompt,
dokładny kontekst i mapę źródeł. Korpus obejmuje 36 prac i 142 recenzje.
Porównano BM25 ze wspólnymi słowami.

## Dane i pochodzenie

Snapshot pobrano przez zalogowaną przeglądarkę. Eksporter API v2
zapisał daty, żądania, schematy, kandydatów i kolejność doboru.
Lokalna kopia: `data/raw/openreview-v3-830dc090e225.json`. SHA-256:
`830dc090e225959047a2619f2c04905131af7c24008aaad1c7e7634d22ce9302`.

| Zbiór | ICLR: prace / recenzje | NeurIPS: prace / recenzje | Łącznie prac / recenzji |
| --- | --- | --- | --- |
| Pierwszy eksport | 30 / 120 | 30 / 115 | 60 / 235 |
| Końcowa próba tematyczna | 16 / 65 | 20 / 77 | 36 / 142 |

Pierwszy eksport obejmuje 1222 notatki. Źródła to 60 abstraktów oraz
235 oficjalnych recenzji. Inne 927 notatek zachowano w raw:
691 Official_Comment, 115 Rebuttal, 60 Decision, 30 Meta_Review,
26 Author_Rebuttal i 5 Public_Comment. Nie są traktowane jak recenzje.
Każda pobrana praca ma od 3 do 6 publicznych oficjalnych recenzji.

Dokładne mapy invitation–submission i oryginalne schematy są w snapshotach.
Audyt: [corpus-audit.json](corpus-audit.json), [rating-scales.json](rating-scales.json).

## Dobór tematu

Pierwszy filtr słów dawał fałszywe trafienia, m.in. vector quantization
audio/obrazu, fine-tuning i bezpieczeństwo. Przegląd objął 104 kandydatów
w kolejności SHA-256, seed=42. Wybrano pierwszych 30 zgodnych prac na konferencję,
bez korzystania z ocen lub późniejszych wyników retrieval.
Decyzje i uzasadnienia: [topic-audit.md](topic-audit.md) oraz
[topic-audit.jsonl](../data/curation/topic-audit.jsonl).

Zakres obejmuje zmniejszanie obliczeń, pamięci, opóźnienia i liczby wywołań
generatywnych LM, kompresję parametrów/kontekstu, serving oraz ocenę jakości
kompresji. Zastosowania multimodalne i dialogowe uwzględniono, jeśli abstrakt
wprost opisuje koszt inferencji części językowej. Wyłączono prace skupione
wyłącznie na treningu, jakości, bezpieczeństwie i reprezentacjach innych danych.

Końcowy korpus obejmuje 36 dostępnych prac z tej listy, wobec
pierwotnie zakładanych 30 + 30. Powodem jest utrzymujący się
`403 ChallengeRequiredError`, potwierdzony w [teście dostępu](access-check.json).
Zadanie podaje 30–50 jako przykład; mniejsza próba obejmuje obie konferencje
i pełne dostępne publiczne recenzje. Nie uzupełniano jej przypadkowymi pracami
spoza zakresu ani wygenerowaną treścią.

Wybrane i brakujące ID: [submission-selection.json](../data/curation/submission-selection.json).
Próba zależy od dostępności, jest nierówna między konferencjami i nie jest
reprezentatywna dla całego obszaru. Nie dobierano jej po wynikach benchmarku.

## Przechowywanie, fragmenty i retrieval

SQLite utrzymuje publikacje, źródła, fragmenty oraz indeks FTS5.
Każdy fragment ma pojedyncze źródło, pole, zakres znaków i hash.
Relacje są kontrolowane kluczami obcymi. Końcowa baza ma 178 źródeł
i 921 fragmentów. Wybrano SQLite ze względu na skalę, pracę na CPU,
brak osobnego serwera i łatwe odtwarzanie, a nie obiecaną przewagę jakościową.

Teksty dzielone są na około 180 słów z overlap=30, osobno w obrębie pola
jednego źródła. BM25 i baseline wspólnych słów mają te same fragmenty,
tokenizację ASCII i listę stopwords. Konferencja i typ źródła są filtrowane
przed top-k. Ranking redukuje się do różnych source ID według najlepszego
chunku. Więcej fragmentów jednej recenzji nie zwiększa liczby źródeł.

Oceny pozostają oryginalne, bez wspólnej skali. ICLR rating obejmuje
1, 3, 5, 6, 8, 10; NeurIPS 1–10. Schematy mają tekstowe etykiety i obiekty
enum z liczbowym `value`. Brak oceny nie jest zerem. Inwentarz skal nie
zastępuje oryginalnych nazw pól ani wartości recenzentów.

## Kontekst i sprawdzone zachowania

Prompt oddziela deklaracje autorów od opinii konkretnych recenzentów.
Abstrakt dołączony do recenzji ma `added_by_relation` i nie zwiększa Hit@5.
Etykieta wskazuje faktycznie przekazany tekst po limicie 12 000 znaków,
konkretną notatkę, publikację i zakres. Treść źródeł to dane, nie instrukcje.

Przykładowa komenda:

```bash
.venv/bin/python -m literature_rag ask "Compare OmniQuant and QLLM quantization limitations" --provider none
```

Powstają ranking, dokładny kontekst, mapa źródeł, końcowy prompt i metadane
przed jakimkolwiek wywołaniem modelu. Końcowe pakiety dla wszystkich
12 pytań wskazuje [submission.json](submission.json).
Domyślna baza to `data/index/real.sqlite`; fikcyjne demo ma osobny plik
`data/index/demo.sqlite` i nie nadpisuje prawdziwego indeksu.

Na danych rzeczywistych sprawdzono filtry, deduplikację, mapy cytowań
i zakresy tekstu. Ponowny import nie powiela rekordów; niezależna odbudowa
daje ten sam fingerprint. SQLite integrity_check zwraca `ok`, a kontrola
kluczy obcych nie wykazuje błędów. Adapter Gemini ma testy na atrapach;
nie wykonano rzeczywistego wywołania dostawcy.

## Ewaluacja

Zestaw obejmuje 10 pytań z odpowiedzią, 2 bez wystarczających danych
i 19 oznaczeń z cytatami oraz uzasadnieniem. ID, fragmenty i filtry
sprawdzono programowo. Metadane oznaczeń są w
[evaluation/metadata.json](../evaluation/metadata.json).
Pytania i oznaczenia nie trafiły do indeksu. Zamrożono ich pliki oraz
fingerprint indeksu w [frozen.json](../evaluation/frozen.json).

Przegląd adnotacji nie był ślepy względem wyniku wstępnego. Nie zmieniano
tekstów pytań, cytatów, trafnych ID ani parametrów wyszukiwania pod uzyskany
wynik. Obie metody uruchomiono na tym samym zamrożonym zestawie.

| Metoda | Trafienia / pytania z odpowiedzią | Hit@5 |
| --- | --- | --- |
| BM25 | 10/10 | 100% |
| Wspólne słowa | 10/10 | 100% |

Jednostką jest konkretna notatka: abstrakt submission albo oficjalna review.
Dwa pytania bez danych nie wchodzą do mianownika. Wyniki per pytanie,
rankingi, score, filtry i czas: [BM25](bm25.json),
[baseline](overlap.json), [porównanie](comparison.md).

Wynik nie dowodzi ogólnej przewagi żadnej metody. Zestaw jest mały,
oznaczenia mogą pomijać inne trafne źródła, a nazwy metod w pytaniach
ułatwiają dopasowanie leksykalne. Jedno oznaczone źródło wystarcza do Hit@5.

## Rzeczywiste porażki i pytania bez danych

**Niekompletne porównania:** q08 (OmniQuant i QLLM) i q09 (SpecExec i Kangaroo)
mają w top-5 obu metod źródła tylko jednej z dwóch prac. To 1/2 pokrycia
mimo Hit@5=1. Prawdopodobną przyczyną jest koncentracja rankingu po słowach OR
bez zapewnienia źródeł obu nazwanych prac. Przy q10 BM25 pokrywa obie prace,
a baseline jedną. Nie wprowadzano poprawki pod te pytania.

**Nietrafne dopasowanie tematu:** robocze zapytanie
`interstellar neutrino detector calibration constant2026` zwróciło recenzje
kwantyzacji przez słowo `calibration`. W lokalnych tekstach nie znaleziono
`neutrino` ani `interstellar`. Zapisano tę zaobserwowaną porażkę przed
benchmarkiem; nie wprowadzono arbitralnego progu score jako wykrywacza wiedzy.
Ranking i pakiet: [observed-failure.json](observed-failure.json).

q11 pyta o energię w J/token z niepewnością dla OmniQuant; q12 o latency QLLM
dla batch=64 i wejścia 131072 tokenów. W abstrakcie i wszystkich recenzjach
właściwych prac brak wymaganych pomiarów; kontrola dotyczy lokalnych źródeł,
nie pełnych PDF-ów. [Skan pól i jednostek](absence-checks.json)
wspiera ręczny przegląd. Obie metody zwracają po 5 fragmentów dla obu pytań,
ale samo dopasowanie słów nie wystarcza do odpowiedzi.

Poparcie twierdzeń i poprawność odmów: **nie oceniano — brak generacji**.
Zachowano rankingi i dokładne prompty, nie zastępując wyników modelu
ręcznie napisanymi odpowiedziami.

## Odtwarzanie i pakiet

Instrukcja oceniającego: [ODDANIE.md](../ODDANIE.md).
Manifest `data/manifests/corpus.json` wskazuje lokalny snapshot
`data/raw/corpus.json`, jego SHA-256 oraz konfigurację indeksu.
Względne ścieżki pozwalają przenieść cały pakiet do innego folderu.

Skrypt `scripts/package_submission.py` dołącza kod, obydwa snapshoty,
końcową bazę, manifest, audyty, zamrożone oznaczenia, wyniki, 12 pakietów
pytań i pakiet nietrafnego zapytania roboczego. Pomija `.env`, `.venv`, `.git`,
cache oraz niepowiązane uruchomienia.
Każdy plik ma SHA-256 w `BUNDLE.json`.
`scripts/verify_submission.py` sprawdza sumy, rozpakowuje do nowego katalogu,
usuwa dołączoną bazę i odtwarza ją offline. Następnie porównuje oba rankingi
i metryki oraz sprawdza zapis nowego promptu i integralność SQLite.
Wynik weryfikacji jest dostarczany obok archiwum.

## Ograniczenia

Próba obejmuje zaakceptowane prace z publicznymi recenzjami i nie jest
reprezentatywnym przeglądem konferencji. Filtr słów może pomijać prace bez
typowego słownictwa, a decyzje tematyczne mają charakter interpretacyjny.
Użyto abstraktów i recenzji, bez PDF-ów. Abstrakt może pochodzić z nowszej
wersji niż recenzja. Opinie recenzentów nie są nieomylnymi opisami prac.
Poprawny technicznie link nie dowodzi poparcia twierdzenia.
