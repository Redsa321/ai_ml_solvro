# Eksport danych z OpenReview

Eksporter odczytuje publiczne dane API v2 z sesji przeglądarki i zapisuje JSON
zgodny z importerem. Przydaje się, gdy klient Python otrzymuje
`403 ChallengeRequiredError`, a przeglądarka ma dostęp po weryfikacji.
Zapisane dane można później importować i przetwarzać bez logowania.

## Uruchomienie

1. Otwórz `https://openreview.net/` i przejdź wymaganą weryfikację.
2. Otwórz konsolę narzędzi deweloperskich.
3. Wczytaj [export-openreview.js](../scripts/export-openreview.js) i uruchom.
4. Zapisz pobrany plik `openreview-snapshot.json`.

W Firefoksie `Ctrl+B` w konsoli włącza edytor wielowierszowy, `Ctrl+O`
wczytuje plik, a `Ctrl+Enter` uruchamia kod. Skrypt musi działać na stronie
`openreview.net`; przeglądarka JSON w domenie `api2.openreview.net` blokuje
dodatkowe żądania przez CSP. Nie trzeba zmieniać ustawień bezpieczeństwa.

Eksporter wykonuje wyłącznie GET do `/groups`, `/notes` i `/invitations`.
Nie odczytuje ani nie zapisuje haseł, cookies i tokenów. Historyczne
formularze recenzji pobiera z `expired=true`.

## Dobór prac

Domyślny wariant pobiera zaakceptowane submissions obu konferencji,
filtruje tytuły i abstrakty pod kątem efektywności inferencji LLM i porządkuje
kandydatów według SHA-256 `42:<note_id>`. Dobiera do 30 prac na konferencję
z publicznymi oficjalnymi recenzjami. Filtr wymaga późniejszego przeglądu
tematycznego; samo słowo kluczowe nie dowodzi zgodności tematu.

Można użyć zapisanej listy kandydatów:

```bash
.venv/bin/python scripts/prepare_browser_export.py --selection data/curation/topic-selection.json
```

Wczytaj w konsoli wygenerowany `runs/export-topic-reviewed.js`.
Eksport dla dokładnej listy zapisze `openreview-topic-reviewed.json`.
Brak wskazanego ID zatrzymuje pobieranie; nie jest zastępowany inną pracą.
Lista obejmuje pierwotnie planowanych 60 kandydatów. Oddawany korpus ma
36 pobranych prac; nie wymaga ponownego eksportu do użycia programu.

## Schematy, błędy i wznawianie

Konfiguracja grupy określa submission ID i nazwę oficjalnej recenzji.
Każda invitation jest pobierana po dokładnym ID i przypisywana do właściwej
publikacji. Publiczne komentarze, decyzje, rebuttale i metarecenzje są
zachowane w raw, ale nie importowane jako recenzje.

403 i 401 zatrzymują pobieranie bez ponawiania. Weryfikację trzeba przejść
oficjalnie w przeglądarce. Timeouty, 429 i 5xx mają maksymalnie trzy próby.
Przy błędzie zapisywany jest plik częściowy z diagnostyką i zebranymi danymi.
Udane żądania są pamiętane w tej samej karcie; zamknięcie lub przeładowanie
karty usuwa cache. Niedobór prac jest jawny, bez rozszerzania tematu.

## Import

```bash
.venv/bin/python -m literature_rag build --snapshot openreview-snapshot.json --db data/index/imported.sqlite
.venv/bin/python -m literature_rag search "KV cache memory" --db data/index/imported.sqlite
```

Końcowy korpus i domyślna baza są opisane w [README](../README.md).
Format eksportu: [SNAPSHOT_FORMAT.md](SNAPSHOT_FORMAT.md).
Źródło protokołu: [dokumentacja API v2](https://docs.openreview.net/how-to-guides/data-retrieval-and-modification/how-to-get-all-notes-for-submissions-reviews-rebuttals-etc).
