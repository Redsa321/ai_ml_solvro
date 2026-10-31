# Uruchomienie i sprawdzenie oddania

Rozpakuj `literature-rag-submission.tar.gz` i wejdź do katalogu `literature-rag`.
Wymagany jest Python 3.12+ z SQLite FTS5. Instalacja pakietów, konto OpenReview
i klucze API nie są potrzebne. Komendy poniżej nie wymagają internetu.

```bash
python3 -m venv --without-pip .venv
.venv/bin/python -m literature_rag search "KV cache memory reduction"
.venv/bin/python -m literature_rag search "quantization limitations" --conference iclr2024 --kind official_review
.venv/bin/python -m literature_rag ask "Compare OmniQuant and QLLM quantization limitations" --provider none
```

`ask` wypisze ścieżkę do promptu, kontekstu i mapy źródeł w `runs/ask-.../`.
Nie generuje odpowiedzi modelu. To dopuszczalny wariant podstawowy zadania.
Domyślna baza `data/index/real.sqlite` zawiera 36 prac i 142 recenzje;
abstrakty i recenzje mają oddzielne role oraz linki do konkretnych notatek.

Odbudowa bazy z lokalnych danych:

```bash
.venv/bin/python -m literature_rag build --manifest data/manifests/corpus.json --db data/index/rebuilt.sqlite
```

Porównanie na zamrożonych pytaniach i oznaczeniach:

```bash
.venv/bin/python -m literature_rag evaluate --frozen evaluation/frozen.json --method bm25 --output runs/check-bm25.json
.venv/bin/python -m literature_rag evaluate --frozen evaluation/frozen.json --method overlap --output runs/check-overlap.json
```

Obie metody uzyskały Hit@5 = 10/10 na 10 pytaniach z odpowiedzią.
Dwa pytania bez danych są oceniane oddzielnie. Wysoki Hit@5 nie oznacza
kompletnej odpowiedzi: q08 i q09 nie mają źródeł obu porównywanych prac w top-5.
Zestaw jest mały, a oznaczenia mogą pomijać inne trafne źródła.

Pełne wyniki i ograniczenia: [raport](reports/raport.md) oraz
[porównanie](reports/comparison.md).
Dokładne przykłady promptów dla wszystkich 12 pytań wskazuje
[reports/submission.json](reports/submission.json).

Pakiet zawiera `BUNDLE.json` z sumami SHA-256 wszystkich dołączonych plików.
Automatyczne sprawdzenie archiwum z poziomu projektu:

```bash
.venv/bin/python scripts/verify_submission.py dist/literature-rag-submission.tar.gz
```

Weryfikator sam tworzy nowy katalog, sprawdza sumy, usuwa dołączoną bazę,
odbudowuje indeks, powtarza porównanie i testuje zapis promptu.
Potwierdzenie wykonania jest dostarczane obok archiwum jako raport weryfikacji.
