# Pobranie przez zalogowaną przeglądarkę

Użytkownik potwierdził, że po zalogowaniu przeglądarka odczytuje JSON API,
podczas gdy proces Python nadal otrzymuje `403 ChallengeRequiredError`.
Eksporter uruchamiamy na stronie **https://openreview.net**, której polityka
pozwala na połączenia do API. Firefox JSON Viewer na `api2.openreview.net`
stosuje `default-src 'none'` i blokuje żądania skryptu. Eksporter odrzuca
tę błędną lokalizację przed pierwszym żądaniem. Działa w istniejącej sesji
przeglądarki i zapisuje publiczne materiały jako lokalny snapshot. Nie odczytuje ani
nie eksportuje haseł, cookies lub tokenów. Wykonuje wyłącznie żądania GET
do `/groups`, `/notes` i `/invitations` w `https://api2.openreview.net`.

## Aktualne uzupełnienie próby tematycznej

Pierwszy pełny eksport został pobrany i zaimportowany. Przegląd tytułów
i abstraktów wykazał prace o innych celach, np. tokenizacji mowy, treningu
i reprezentacjach wizualnych. Przegląd objął 104 kandydatów w kolejności
seed=42; wybrano docelowe 30 prac z każdej konferencji. Są to decyzje
asystenta zapisane w [topic-audit.jsonl](../data/curation/topic-audit.jsonl),
bez deklaracji przeglądu przez człowieka.

Mamy już recenzje dla 36 docelowych prac. Dla kolejnych 24 trzeba pobrać
publiczne wątki i schematy. Wersja v4 eksportera obsługuje konkretną listę ID:

```bash
.venv/bin/python scripts/prepare_browser_export.py --selection data/curation/topic-selection.json
```

Po odzyskaniu internetu, na stronie konferencji z instrukcji poniżej,
wczytaj **`runs/export-topic-reviewed.js`** zamiast ogólnego skryptu.
Uruchom go przez Ctrl+Enter. Powinien wypisać `exporter v4: topic-reviewed ID list`.
Zapisze `openreview-topic-reviewed.json`, a przy błędzie `openreview-topic-partial.json`.
Zachowanie tej samej karty pozwala wykorzystać cache udanych żądań.

Lista [topic-selection.json](../data/curation/topic-selection.json) zawiera
identyfikatory i regułę doboru. Eksporter nie zastępuje brakującego ID inną
pracą. Zakres obejmuje koszt inferencji, kompresję modelu/kontekstu, serving
i ocenę jakości kompresji; nie wybiera prac według ocen recenzentów.
Raport decyzji jest w [reports/topic-audit.md](../reports/topic-audit.md).

## Jednorazowe uruchomienie

1. W zalogowanej przeglądarce otwórz
   [stronę konferencji ICLR](https://openreview.net/group?id=ICLR.cc/2024/Conference).
   Adres strony musi zaczynać się od `https://openreview.net/`.
2. Otwórz narzędzia deweloperskie przez F12 i przejdź do zakładki Console.
3. W Firefox kliknij przy `>`, naciśnij **Ctrl+B**, a następnie **Ctrl+O**.
   Wczytaj aktualny [scripts/export-openreview.js](../scripts/export-openreview.js)
   z folderu projektu i uruchom przez **Ctrl+Enter**. Wczytaj plik ponownie,
   jeśli edytor konsoli nadal pokazuje starszą wersję skryptu.
4. Zostaw kartę otwartą. Postęp pojawi się w konsoli. Skrypt stronicuje
   metadane, wybiera kandydatów i pobiera publiczne wątki oraz schematy recenzji.
5. Po zakończeniu przeglądarka pobierze `openreview-snapshot.json`.
   Przenieś plik do `data/raw/openreview-snapshot.json` w projekcie.

Nie trzeba przenosić sesji przeglądarki do Pythona ani podawać hasła w rozmowie.
Node nie jest wymagany do uruchomienia eksportera w przeglądarce; służy
wyłącznie do jego lokalnych testów.

### Firefox: otwarcie pliku w konsoli

Firefox pozwala wczytać skrypt bezpośrednio z pliku. Kliknij przy znaku `>`
w konsoli, naciśnij **Ctrl+B**, aby otworzyć edytor wielowierszowy, następnie
**Ctrl+O** i wybierz `scripts/export-openreview.js` w tym projekcie.
Uruchom wczytany kod przez **Ctrl+Enter**. Pozostań na stronie konferencji
w domenie `openreview.net` podczas tej operacji. Są to skróty opisane w
[dokumentacji konsoli Firefox](https://firefox-source-docs.mozilla.org/devtools-user/web_console/the_command_line_interpreter/index.html#multi-line-mode).

## Co znajduje się w eksporcie

- Cel: po 30 zaakceptowanych prac ICLR 2024 i NeurIPS 2024, z co najmniej
  jedną publiczną oficjalną recenzją na pracę.
- Temat jest filtrowany po tytule i abstrakcie: modele językowe oraz mechanizmy
  lub metryki kosztu inferencji. Pełna reguła jest w funkcji `topicMatch`;
  wybrana próba nadal wymaga ręcznego przeglądu trafności tematu.
- Kolejność kandydatów: rosnące SHA-256 z `42:<note_id>`. Nie zależy od ocen
  recenzji ani wyników przyszłego benchmarku.
- Typ recenzji jest odkrywany z `review_name` grupy. Sam sufiks nie wystarcza:
  skrypt pobiera dokładny obiekt invitation, sprawdza strukturę schematu,
  forum i bezpośrednie powiązanie notatki z submission.
- Dla zamkniętych formularzy konferencji z 2024 roku używa `expired=true`.
  Bez tego parametru API zwraca `400 InvitationExpiredError`, mimo że
  historyczne recenzje pozostają publiczne. Parametr nie zmienia formularza.
- Pola ocen są rozpoznawane z typów liczbowych i liczbowych skal enum w
  rzeczywistych schematach. Oryginalne obiekty invitations i pełne `content`
  recenzji zostają zachowane. Nietypowe skale należy sprawdzić w audycie.
- Wszystkie dostępne publiczne oficjalne recenzje wybranych prac pozostają
  w eksporcie, obok innych publicznych replies. Importer oddzieli ich typy.
- `provenance` zapisuje daty, żądania, kandydatów, wykluczenia i wybrane ID.
  Żadne dane uwierzytelniające nie są dołączane do tych zapisów.

Status ogólnego eksportu to `complete_pending_topic_audit`; dla zadanej listy ID
to `complete_with_topic_selection`. Żaden nie oznacza zakończenia projektu.
Przed zamrożeniem benchmarku trzeba przeczytać wybrane tytuły,
abstrakty, przykładowe recenzje i skale, a następnie potwierdzić poprawność
próby oraz relacji. Dopiero na rzeczywistym korpusie powstaną pytania końcowe.

## Gdy pobieranie się zatrzyma

Pierwszy plik `openreview-partial.json` zapisany w głównym folderze projektu
zawierał zero notatek i zero udanych żądań: Firefox zablokował pierwszy fetch
w JSON Viewerze. To problem kontekstu uruchomienia, a nie brak recenzji.
Otwórz stronę konferencji z kroku 1 i wczytaj z dysku aktualną wersję eksportera.
Sprawdzono nagłówki strony: `connect-src` dopuszcza `https://api2.openreview.net`,
a API zwraca `Access-Control-Allow-Origin: https://openreview.net` i
`Access-Control-Allow-Credentials: true`. Nie wymaga to zmiany ustawień CSP.

Kolejny eksport w wersji v2 pobrał metadane 2260 prac ICLR i pierwszy wątek,
lecz zatrzymał się na zamkniętym formularzu recenzji. Wersja v3 pobiera
schematy z `expired=true` i zachowuje nazwy błędów API w `failed_requests`.
Rozpoznaje też skale takie jak `3 good`, oprócz formatów `6: ...`.
Filtr tematu wymaga mechanizmu lub metryki efektywności: samo wystąpienie
`decoding` lub `inference` w pracy o modelach językowych nie wystarcza.
Dodano `candidate_submissions`, aby zachować pełne metadane kandydatów
także w częściowym eksporcie.

Przy ponowieniu w tej samej karcie wczytaj plik skryptu z dysku jeszcze raz,
aby edytor konsoli użył aktualnej wersji. Skrypt wypisze `exporter v4`.
Pobrane poprawnie strony metadanych zostaną odtworzone z cache karty.

HTTP 403 lub 401 zatrzymuje pobieranie bez ponawiania tego błędu. Przy 403
przejdź wymaganą weryfikację oficjalnie w przeglądarce; skrypt jej nie omija.
Timeouty, problemy sieci, 429 i błędy serwera mają najwyżej trzy próby.

Przy błędzie przeglądarka pobierze `openreview-partial.json`. Zachowaj go
również wtedy, gdy ma mało prac: zawiera diagnostykę i dostępne raw schematy.
W trakcie pobierania zawartość robocza jest dostępna jako `openreviewSnapshot`.
Zostawienie tej samej karty pozwala ponownie uruchomić skrypt z cache
udanych żądań, bez ponownego pobierania już dostępnych odpowiedzi.
Cache jest w pamięci karty; przeładowanie lub zamknięcie karty go usuwa.

Jeżeli temat daje mniej niż 30 kwalifikujących się prac, eksporter zapisze
wynik częściowy i pokaże brak. Nie rozszerza samodzielnie tematu i nie
uzupełnia braków fikcyjnymi publikacjami. Taki przypadek wymaga analizy
listy kandydatów i uzgodnienia dalszego doboru.

## Import do aplikacji

Po umieszczeniu pobranego pliku w projekcie:

```bash
.venv/bin/python -m literature_rag build --snapshot data/raw/openreview-snapshot.json --db data/index/real.sqlite
.venv/bin/python -m literature_rag doctor --db data/index/real.sqlite
.venv/bin/python -m literature_rag search "KV cache memory limitations" --db data/index/real.sqlite --kind official_review
```

Indeks demonstracyjny pozostaje osobno w `data/index/corpus.sqlite`.
Format eksportu opisuje [SNAPSHOT_FORMAT.md](SNAPSHOT_FORMAT.md).

Źródło protokołu: [dokumentacja pobierania API v2 OpenReview](https://docs.openreview.net/how-to-guides/data-retrieval-and-modification/how-to-get-all-notes-for-submissions-reviews-rebuttals-etc).
Eksporter sprawdzono na lokalnym sztucznym API i w teście zgodności z
importerem Python. Użytkownik pobrał już pierwszy pełny eksport przez swoją
sesję; agent sprawdził i zaimportował ten plik lokalnie. Uzupełnienie listy
tematycznej jest przygotowane i wymaga uruchomienia po odzyskaniu sieci.
