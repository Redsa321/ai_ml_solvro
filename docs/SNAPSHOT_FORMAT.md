# Lokalny snapshot OpenReview

`build --snapshot plik.json` przyjmuje plik z trzema częściami: pochodzeniem,
zweryfikowanymi mapami invitations oraz oryginalnymi notatkami API v2.
Przykładem kształtu danych jest
[synthetic_snapshot.json](../tests/fixtures/synthetic_snapshot.json), wyraźnie
oznaczony jako fikcyjny. Nie kopiuj z niego schematów jako potwierdzonych dla
prawdziwych konferencji; wymagają sprawdzenia na rzeczywistych submissions,
invitations i reviews po odzyskaniu dostępu.

## Nagłówek i pochodzenie

- `schema_version`: liczba `1`.
- `dataset_type`: `openreview` dla prawdziwego pobrania albo `synthetic` dla fixtures.
- `provenance.fetched_at`: data pobrania ISO 8601 z jawną strefą czasową.
- `provenance.selection_method`: zapisane kryteria wyboru i kolejności próby.
- Pozostałe dane pochodzenia, np. seed, URL-e żądań, ID kandydatów,
  wykluczenia i powody, można dopisać do `provenance`; zostają w metadanych.

Importer identyfikuje raw plik hashem SHA-256 i zachowuje wszystkie notatki
w oryginalnym snapshotcie, nawet gdy nie są indeksowane. Korpus ma osobny
fingerprint znormalizowanych publikacji i źródeł. Indeks ma fingerprint
uwzględniający również chunking, preprocessing i wersję schematu.

## `venues`: jawne potwierdzenie typów

Każdy obiekt zawiera `id` konferencji, `year=2024`, `submission_invitation`,
`verified=true`, `verification_note`, `rating_fields` oraz `review_invitations`.

`review_invitations` jest obiektem mapującym **dokładny invitation ID** na
**submission note ID** właściwej pracy. Nazwa kończąca się `Official_Review`
nie wystarcza. Także poprawna invitation z innej pracy nie może przypiąć do
niej recenzji tylko dlatego, że ta ma podobny tekst lub tytuł.

`verification_note` opisuje, jak sprawdzono schemat. `rating_fields` to
oryginalne nazwy pól ocen tej konferencji. Ich wartości, włącznie z wrapperem
`{"value": ...}`, są przechowywane w `ratings` bez przeskalowania. Brakująca
ocena nie jest dodawana. Pozostałe niepuste pola tekstowe recenzji trafiają
do `sections`, a pełne `content` pozostaje zachowane, również dla nieznanych pól.

## `notes`: oryginalne notatki

Lista zawiera submissions i replies z lokalnego eksportu API v2.
Notatka ma `id`, `forum`, listę `invitations`, obiekt `content` i listę `readers`.
W tym projekcie akceptujemy do indeksu wyłącznie notatki z `everyone` w `readers`.

Submission wymaga tekstowych `title` i `abstract` oraz `content.venueid`
równego identyfikatorowi wybranej konferencji, czyli statusu accepted.
Wartości API v2 są odczytywane z `content[nazwa].value`.

Oficjalna recenzja musi mieć invitation obecną w mapie, `forum` zgodne
z przypisaną pracą oraz `replyto` równe jej submission note ID. Musi też
zawierać przynajmniej jedno tekstowe pole inne niż pola ocen. Każda wybrana
publikacja potrzebuje co najmniej jednej takiej publicznej recenzji.

Komentarze, decyzje, rebuttale i metarecenzje pozostają w raw, ale nie stają
się źródłami. Ich liczba jest widoczna w `import_report.ignored_other_replies`.
Brak tekstu recenzji jest liczony oddzielnie. Duplikaty ID, niezgodne relacje,
prywatne źródła i brak wymaganych danych kończą import czytelnym błędem.

Pełne oryginalne notatki i pozostałe pola zachowuje raw JSON. SQLite przechowuje
pełne `content`, invitations i dostępne `cdate/mdate/tcdate/tmdate` dla
indeksowanych źródeł. Najnowszy abstrakt może pochodzić z późniejszej wersji
niż recenzja; aplikacja nie zakłada zgodności czasowej tych wersji.

## Odtworzenie

Zachowaj raw JSON wraz z manifestem wygenerowanym przez `build`.
`build --manifest ... --db ...` weryfikuje hash raw pliku i korpusu,
odczytuje zapisaną konfigurację i odtwarza indeks bez internetu. Ścieżka
snapshotu w manifeście jest względna wobec położenia manifestu.

Import tego samego korpusu i konfiguracji nie dodaje duplikatów. Zapis nowego
indeksu jest atomowy; błąd importu nie niszczy poprzedniej bazy. Zmiana treści
lub konfiguracji wymaga nowego pliku `--db` albo jawnego `--replace`.
