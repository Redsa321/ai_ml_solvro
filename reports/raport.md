# Asystent literatury OpenReview — raport roboczy

Stan na 2026-10-30. Program działa offline na rzeczywistych danych.
Docelowy korpus i końcowa ewaluacja pozostają do dokończenia.

## Dane i pochodzenie

Użytkownik pobrał snapshot przez zalogowaną przeglądarkę. Eksporter zapisał
daty, żądania, schematy, kandydatów i kolejność doboru. Lokalna kopia to
`data/raw/openreview-v3-830dc090e225.json`. SHA-256:
`830dc090e225959047a2619f2c04905131af7c24008aaad1c7e7634d22ce9302`.

| Zbiór | ICLR: prace / recenzje | NeurIPS: prace / recenzje | Łącznie prac / recenzji |
| --- | --- | --- | --- |
| Pierwszy pełny eksport | 30 / 120 | 30 / 115 | 60 / 235 |
| Dostępna próba po przeglądzie tematu | 16 / 65 | 20 / 77 | 36 / 142 |

Pełny eksport obejmuje 1222 notatki. Do źródeł trafiło 60 abstraktów oraz
235 oficjalnych recenzji. Pozostałe 927 notatek zachowano w raw:
691 Official_Comment, 115 Rebuttal, 60 Decision, 30 Meta_Review,
26 Author_Rebuttal i 5 Public_Comment. Nie są traktowane jak recenzje.
Każda praca ma od 3 do 6 publicznych oficjalnych recenzji.

Inwentarz identyfikatorów i konfiguracji jest w `data/manifests/`.
Audyt struktury i skal: [corpus-audit.json](corpus-audit.json) oraz
[rating-scales.json](rating-scales.json). Surowe schematy są w snapshotcie.

## Dobór tematu

Pierwszy filtr słów w tytule i abstrakcie dawał fałszywe trafienia, m.in.
vector quantization reprezentacji audio/obrazu, fine-tuning i bezpieczeństwo.
Asystent przejrzał 104 kandydatów z udokumentowanej kolejności SHA-256,
seed=42. Wybrano pierwszych 30 prac zgodnych z przyjętym zakresem na konferencję.
Nie korzystano z ocen recenzji ani wyników retrieval do tego wyboru.

Zakres obejmuje zmniejszanie obliczeń, pamięci, opóźnienia i liczby wywołań
generatywnych LM, kompresję parametrów/kontekstu, serving oraz ocenę jakości
kompresji. Uwzględniono zastosowania multimodalne i dialogowe, jeśli abstrakt
wprost opisuje koszt inferencji części językowej. Wyłączono prace skupione
wyłącznie na treningu, jakości, bezpieczeństwie i reprezentacjach innych danych.

Decyzje i uzasadnienia: [topic-audit.md](topic-audit.md) oraz
[topic-audit.jsonl](../data/curation/topic-audit.jsonl).
Są to decyzje asystenta, bez deklaracji weryfikacji przez człowieka.
Mamy 36 z 60 docelowych prac. Recenzje dla pozostałych 24 są do pobrania
przez przygotowany eksporter, gdy wróci internet.

## Przechowywanie i retrieval

SQLite utrzymuje publikacje, źródła i fragmenty oraz indeks FTS5.
Każdy fragment ma pojedyncze źródło, pole, zakres znaków i hash.
Relacje są kontrolowane kluczami obcymi. Baza tematyczna ma 178 źródeł
i 921 fragmentów; pełna baza pierwotnego eksportu ma 295 źródeł i 1533 fragmenty.

BM25 i baseline wspólnych słów korzystają z tego samego preprocessingu,
fragmentów i filtrów. Konferencja i typ źródła są filtrowane przed top-k.
Ranking jest redukowany do różnych source ID; kilka fragmentów jednej
recenzji daje jedno źródło. Metody leksykalne nie gwarantują trafności parafraz.

Oceny pozostają w oryginalnej postaci, bez wspólnej skali. ICLR rating
obejmuje wartości 1, 3, 5, 6, 8, 10; NeurIPS obejmuje 1–10. Schematy mają
zarówno tekstowe etykiety, jak i obiekty enum z liczbowym `value`.
Wartości w inwentarzu skal nie zastępują oryginalnych zapisów recenzentów.

## Sprawdzone zachowania

Na prawdziwej próbie tematycznej wykonano sześć uruchomień: trzy zapytania
robocze dla BM25 i wspólnych słów. Sprawdzono filtr konferencji,
deduplikację źródeł oraz mapę etykieta–fragment–recenzja–publikacja.
Każdy fragment kontekstu zgadza się z zapisanym zakresem tekstu źródła.
Są to testy działania, nie końcowe wyniki jakości.

Ponowny import nie powiela rekordów. Niezależna odbudowa z lokalnego
snapshotu daje ten sam fingerprint indeksu. SQLite integrity_check
zwraca `ok`, a kontrola kluczy obcych nie wykazuje błędów.
Pakiety promptów i dowody: [data-validation.json](data-validation.json).

Przykładowe działające polecenie:

```bash
.venv/bin/python -m literature_rag ask "Compare OmniQuant and QLLM quantization limitations" --db data/index/topic-reviewed-partial.sqlite --provider none
```

Pakiet zapisuje ranking, dokładny kontekst, mapę źródeł i końcowy prompt.
Nie powstaje odpowiedź udająca generację modelu. Generowanie przez Gemini
nie zostało uruchomione; adapter ma testy na atrapach transportu.

## Rzeczywisty nietrafny wynik

Zapytanie robocze `interstellar neutrino detector calibration constant2026`
zwróciło recenzje metod kwantyzacji przez wspólne słowo `calibration`.
W tekstach próby tematycznej nie znaleziono `neutrino` ani `interstellar`.
Wynik leksykalny nie daje podstaw do odpowiedzi na pytanie o pomiary fizyczne.
To ograniczenie wyszukiwania po słowach z operatorem OR; nie wprowadzono
arbitralnego progu score jako wykrywacza braku wiedzy.

Przypadek i źródła zapisano w `observed_failure` w raporcie walidacji.
To przykład rozwojowy, nie pytanie końcowego benchmarku. Zachowanie
generowanego tekstu przy takim kontekście pozostaje do sprawdzenia.

## Stan ewaluacji

Przygotowano [szkic](../evaluation/draft/review.md) obejmujący 10 pytań
z odpowiedzią, 2 bez wystarczających danych i 19 oznaczeń źródeł.
ID, cytaty i filtry zweryfikowano programowo na dostępnej bazie.
Szkic jest propozycją asystenta, niezamrożoną i wymagającą sprawdzenia
przez człowieka oraz ponownej walidacji po uzupełnieniu korpusu.
Nie dodano pytań ani oznaczeń do indeksu.

Hit@5: **nie raportowano końcowego wyniku** — benchmark nie jest zamrożony.
Poparcie twierdzeń: **nie oceniano — brak generacji**.
Nie zastępujemy tego wyniku ręcznie napisanymi odpowiedziami.

Po ukończeniu korpusu i przeglądzie oznaczeń należy zamrozić pliki oraz
uruchomić obie metody na tej samej bazie i pytaniach. Raport powinien podać
licznik i mianownik Hit@5, wynik per pytanie oraz ograniczenia oznaczeń.
Przy generacji potrzebna jest ręczna ocena rzeczywistych twierdzeń względem
przywołanych fragmentów. Dwa pytania bez danych oceniamy oddzielnie.

## Ograniczenia

Próba obejmuje zaakceptowane prace z publicznymi recenzjami i nie jest
reprezentatywnym przeglądem całych konferencji. Filtr słów może pomijać prace
bez typowego słownictwa, a decyzje tematyczne mają charakter interpretacyjny.
Użyto abstraktów i recenzji, bez pełnych PDF-ów. Abstrakt może pochodzić
z nowszej wersji niż recenzja. Opinie recenzentów nie są nieomylnymi opisami
prac. Nawet poprawny technicznie link nie dowodzi poparcia twierdzenia.
