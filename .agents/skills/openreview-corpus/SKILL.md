---
name: openreview-corpus
description: Pobieraj, normalizuj i odtwarzaj korpus publikacji i oficjalnych recenzji OpenReview w tym projekcie. Używaj przy doborze próby, weryfikacji schematów konferencji i imporcie danych; nie do samego rankingu ani ewaluacji odpowiedzi.
---

# Korpus OpenReview

Odczytaj ustalenia korpusu i etap E1–E2 w [PLAN.md](../../../PLAN.md).
Wymagania źródłowe są w [zadanie.md](../../../zadanie.md).

## Najpierw dostęp i rzeczywisty schemat

- Użyj API v2 i oficjalnej [instrukcji pobierania](https://docs.openreview.net/how-to-guides/data-retrieval-and-modification/how-to-get-all-notes-for-submissions-reviews-rebuttals-etc).
  Publiczne dane pobieraj bez logowania, jeśli serwis na to pozwala.
- Pobierz group konferencji i odczytaj `submission_name`, `review_name`
  oraz identyfikatory statusów z `content`. Nie zgaduj nazw invitations.
- Przed pełnym pobraniem sprawdź kilka submissions i replies z obu konferencji.
  Zapisz prawdziwe nazwy pól i ich typy. `content[field].value` rozpakowuj
  bez utraty oryginalnej struktury; zachowaj także nieznane pola.
- `403 ChallengeRequiredError` wymaga oficjalnej weryfikacji użytkownika.
  Zatrzymaj ten typ żądania, opisz stan i kontynuuj pracę offline. Nie stosuj
  obejść challenge ani zapętlonych ponowień. Konto samo nie gwarantuje rozwiązania.
- Dla timeoutów, 429 i błędów 5xx użyj ograniczonych ponowień i checkpointu.
  Odróżniaj niedostępność sieci, brak uprawnień i brak publicznych recenzji.

## Dobór i normalizacja

- Punktem wyjścia jest 30 zaakceptowanych prac z każdej konferencji z co
  najmniej jedną publiczną oficjalną recenzją. Filtr tematu, kolejność kandydatów,
  seed i powody odrzucenia zapisuj; nie wybieraj danych pod późniejsze pytania.
- Kandydatów dobieraj po tytule i abstrakcie, nie po wysokości ocen lub
  atrakcyjności uwag recenzenta. Niedobór prac zgłoś zamiast cicho zmieniać temat.
- Rozpoznawaj oficjalną recenzję po potwierdzonej invitation należącej do
  właściwej konferencji i submission. Sprawdź `forum` i `replyto`.
  Sufiks bez potwierdzenia schematu nie jest wystarczającą klasyfikacją.
- Metarecenzje, komentarze, odpowiedzi autorów i decyzje zachowuj w raw, lecz
  nie importuj jako oficjalne recenzje. Nie imputuj brakujących pól ani ocen.
- Zachowaj note ID, forum ID, invitation IDs, źródłowy URL, timestampy notatki
  i pobrania oraz oryginalne pola ocen. Przechowaj teksty i oceny oddzielnie;
  nie porównuj liczbowo różnych skal bez mapowania.
- Zapisz raw odpowiedzi API przed normalizacją i manifest wybranych ID.
  Snapshot identyfikuj hashami treści, nie samą datą pobrania.

## Wynik pracy

Oddaj lokalny snapshot, manifest doboru, adaptery potwierdzonych schematów
i raport jakości: liczba prac i recenzji per konferencja, braki, wykluczenia,
duplikaty i osierocone relacje. Zachowaj informację, że najnowszy abstrakt
może pochodzić z innej wersji pracy niż moment napisania recenzji.

Sprawdź import dwa razy na tych samych danych: liczności i hash korpusu mają
pozostać takie same. Zweryfikuj odtworzenie bazy z lokalnego snapshotu bez sieci
oraz odrzucenie recenzji przypiętej do niewłaściwej pracy. Sztuczne fixtures
oznacz jako testowe; nie przedstawiaj ich jako danych pobranych z konferencji.
