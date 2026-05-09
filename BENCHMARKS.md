# Benchmarks

Run on your machine with:

```powershell
anagram bench
```

Example output from the bundled English dictionary:

```text
words,41
sorted,0.034
counter,0.158
prime,0.027
```

The bundled dictionary is intentionally tiny, so these numbers are only a smoke test. Use a large
word list with `--dictionary` to compare strategies meaningfully.
