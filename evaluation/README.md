# Przygotowanie benchmarku

Na podstawie lokalnego korpusu 36 prac przygotowano
[szkic do sprawdzenia](draft/review.md): 10 pytań z odpowiedzią, 2 bez danych
i 19 oznaczeń rzeczywistych źródeł. To propozycja asystenta, oznaczona
`human_reviewed=false`, niezamrożona i nieużyta do końcowego porównania.
Metadane i fingerprint bieżącego korpusu są w [draft/metadata.json](draft/metadata.json).
Po uzupełnieniu 24 prac potrzebna jest ponowna walidacja oraz przegląd
oznaczeń przez człowieka. Pliki końcowe `questions.jsonl` i `judgments.jsonl`
pozostają do przygotowania po tej weryfikacji.

Przykłady w `tests/fixtures` są odrębnymi danymi fikcyjnymi do testowania kodu.

## Pytania: `questions.jsonl`

Jeden obiekt JSON w wierszu. Wymagane: unikalny `question_id`, angielski
tekst `question` i logiczne `answerable`. Opcjonalne: `conference` jako alias
lub pełny venue ID oraz `kind` równe `author_abstract` lub `official_review`.
Typ pytania można opisać dodatkowym polem `type`.

Dla `answerable=false` wymagane są `absence_reason` i `absence_check`:
czego brakuje oraz jak sprawdzono brak w całym lokalnym korpusie. Sam brak
wyniku BM25 nie jest wystarczającą weryfikacją.

## Oznaczenia: `judgments.jsonl`

Każde oznaczenie zawiera `question_id`, konkretny `source_id`, ręczne
uzasadnienie `reason` i dosłowny fragment `evidence` występujący w jednej
sekcji źródła. Dla abstraktu ID jest identyfikatorem submission, a dla recenzji
jej własnym note ID. Recenzje tej samej publikacji nie są zamienne.

Każde pytanie z odpowiedzią wymaga co najmniej jednego trafnego źródła.
Przy porównaniu dwóch prac oznacz źródła obu. Pytania bez danych nie mają
trafnych źródeł. `freeze` sprawdza istnienie ID, zgodność filtrów i występowanie
cytatu. Nie zastępuje ręcznej oceny, czy treść rzeczywiście odpowiada na pytanie.

## Zamrożenie i porównanie

1. Ustal parametry na osobnych pytaniach roboczych.
2. Przeczytaj źródła i przygotuj minimum 10 pytań z odpowiedzią oraz 2 bez danych.
3. Ręcznie sprawdź oznaczenia i uruchom `freeze` zgodnie z README projektu.
4. Uruchom obie metody z tym samym plikiem `--frozen` i bazą.
5. Zachowaj oba pliki wynikowe, błędy i interpretację w raporcie.

Zamrożenie zapisuje hashe pytań, oznaczeń i indeksu. Nie nadpisuje istniejącego
pliku: poprawki wymagają nowej wersji i ponownego porównania obu metod.
Do krótszych rzeczywistych zestawów roboczych służy `--development`.
`--allow-synthetic` jest wyłącznie testem narzędzi i daje `synthetic_test_only`.

Hit@5 ocenia top-5 różnych źródeł. Raport zawiera licznik i mianownik oraz
wyniki per pytanie. Pytania bez danych nie wchodzą do mianownika. Jedno
trafienie przy porównaniu dwóch prac nie oznacza kompletnych dowodów dla obu.
Niepełne oznaczenia ograniczają interpretację, a dziesięć pytań nie uzasadnia
silnych wniosków statystycznych.

## Ocena odpowiedzi

Oceniaj wyłącznie zapisane odpowiedzi rzeczywiście wygenerowane przez model,
korzystając z przekazanego mu kontekstu. Ręcznie wypisz sprawdzalne twierdzenia
i oznacz `supported`, `unsupported` lub `contradicted`, wraz z przywołanymi
etykietami i uzasadnieniem. `supported` wymaga poparcia w przywołanym fragmencie.
Twierdzenie bez cytowania nie może zniknąć z mianownika.

Podać supported/wszystkie sprawdzalne twierdzenia; przy zerowym mianowniku
„nie dotyczy”. Odmowy, twierdzenia nieweryfikowalne oraz pytania bez danych
opisać oddzielnie. Przy braku generacji wynik brzmi „nie oceniano — brak
generacji”. Atrapy odpowiedzi w testach adaptera nie są wynikami modelu.
