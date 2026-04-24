# Anagram Detector

A small, typed Python CLI that demonstrates dataclasses, frozen hashable domain objects,
composable normalization strategies, interchangeable signature strategies, dictionary
repositories, disk caching, and argparse subcommands.

## Install

From this folder:

```powershell
python -m pip install -e .
```

Then run:

```powershell
anagram check listen silent
```

You can also run without installing by setting `PYTHONPATH` to the source directory:

```powershell
$env:PYTHONPATH = "src"
python -m anagram_detector check listen silent
```

## Examples

```powershell
anagram check "Dormitory" "Dirty room!!"
anagram find listen
anagram --min-length 2 sub listen
anagram multi conversation --max-words 3
anagram group words.txt
Get-Content words.txt | anagram group -
anagram --format json find café
anagram --language fr find café
anagram bench
anagram cache info
anagram cache clear
```

## Dictionaries And Languages

The package ships with small bundled `en`, `es`, and `fr` dictionaries for zero-config use.
For larger searches, pass your own word list:

```powershell
anagram --dictionary C:\words\english.txt find triangle
```

Dictionary files are streamed line by line. The search index is built once and cached under
`~/.anagram/cache` by default.

## Configuration

Optional config file: `~/.anagram/config.toml`.

```toml
language = "en"
strategy = "sorted"
format = "plain"
cache_dir = "~/.anagram/cache"
normalizers = ["casefold", "whitespace", "punctuation", "diacritics", "nonalpha"]
```

Precedence is:

1. CLI flags
2. `~/.anagram/config.toml`
3. Hardcoded defaults

## Signature Strategies

`sorted` is the readable baseline. `counter` keeps frequency information in a hashable form.
`prime` uses prime multiplication for ASCII letters, with a fallback for non-ASCII inputs.

Benchmark locally with:

```powershell
anagram bench
```

## Cache Policy

The disk cache stores pickled indexes. Cache keys include the dictionary content hash, the
normalization pipeline, and the signature strategy, so source changes automatically produce a
new cache file. There is no automatic eviction policy; use `anagram cache clear` to remove old
cache files. Cache files are intended for trusted local environments only.
