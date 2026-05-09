# Architecture Decision Record

## App 30 — Anagram Detector

**Utility Apps Group | Document 1 of 5**  
**Status: Accepted**  
**Date: 2026-05-09**

## Title

Use a normalized-signature engine with pluggable strategies, dictionary repositories, disk-cached indexes, and an argparse CLI for anagram detection.

## Context

The Anagram Detector began with a simple problem: determine whether two strings are anagrams by checking whether they contain the same letters in the same frequencies. The finished app expands that core idea into a small typed Python package that supports direct pair comparison, dictionary-backed exact anagram search, sub-anagram search, multi-word anagram search, ad-hoc grouping of a provided word list, benchmarking of signature algorithms, and cache management.

The repository is organized as a Python package under `src/anagram_detector`. The package exposes the reusable detector API through `AnagramDetector`, `AnagramIndex`, domain result objects, and custom exceptions. It also installs a console script named `anagram`, with `python -m anagram_detector` as a source-tree execution path.

The main architectural constraint was to keep the project understandable as an academic CLI app while still showing growth beyond a one-function exercise. A pure two-string function would solve the smallest version of the problem, but it would not demonstrate layered design, reusable domain objects, strategy patterns, repository boundaries, caching, or robust CLI behavior.

## Decision Drivers

- **Correctness of anagram comparison**: two inputs should match only when their normalized character frequencies/signatures match.
- **Clear separation of concerns**: normalization, signature generation, dictionary loading, index construction, querying, formatting, and CLI parsing should remain independent.
- **Extensibility**: the app should support multiple normalization pipelines and signature strategies without rewriting the detector engine.
- **Beginner-readable architecture**: each module should have a narrow purpose and use Python standard library tools before adding dependencies.
- **Typed, testable core**: the domain and engine should be usable directly from tests and library callers without invoking the CLI.
- **Efficient repeated dictionary search**: dictionary indexes should be built once and reused through a local disk cache.
- **Safe enough local persistence**: cache files may use pickle because they are local implementation artifacts, but the runbook must document the trust boundary.
- **Zero-config operation**: bundled dictionaries should make common commands work immediately after install.
- **Portfolio value**: the app should demonstrate dataclasses, protocols, strategies, repositories, caching, subcommands, stdin/file handling, and JSON/CSV output.

## Options Considered

### Option 1 — Sort both strings directly in one function

A minimal anagram detector can normalize two strings, sort their characters, and compare the resulting strings.

**Chosen / Rejected:** Rejected as the whole architecture.

**Reason:** Sorting is an excellent baseline signature strategy, but placing all logic in one function would prevent clean extension to dictionary indexing, grouped results, alternate strategies, caching, and multiple CLI modes.

### Option 2 — Use `collections.Counter` everywhere

A frequency map directly represents the mathematical definition of an anagram and can compare two strings in linear time.

**Chosen / Rejected:** Rejected as the only representation, accepted as one strategy.

**Reason:** Counter-based signatures are useful, but a raw `Counter` is mutable and not directly hashable for dictionary keys. The implemented `CounterSignature` converts frequency data to a `frozenset[tuple[str, int]]`, preserving the benefits while keeping the result usable in indexes.

### Option 3 — Prime multiplication as the default signature

The prime-product trick maps each letter to a prime and multiplies values. Anagrams produce the same product.

**Chosen / Rejected:** Rejected as the default, accepted as a benchmarkable strategy.

**Reason:** Prime signatures are interesting and fast for short ASCII words, but they grow very large for long inputs and require a fallback for non-ASCII letters. Keeping it as an optional strategy allows the app to teach the idea without making it the most reliable default.

### Option 4 — Build dictionary indexes every run

The app could stream dictionaries and build the signature index every time a search command runs.

**Chosen / Rejected:** Rejected.

**Reason:** This is simple but inefficient. Rebuilding on each run would make `find`, `sub`, and `multi` slower with larger dictionaries. A disk cache is a better fit because dictionary content, normalization pipeline, and signature strategy can form a stable cache identity.

### Option 5 — Store the dictionary cache as JSON

JSON would make cache files inspectable and safer than pickle.

**Chosen / Rejected:** Rejected for this version.

**Reason:** The cache stores Python domain objects, hashable signatures, and nested structures that are easier to preserve with pickle. JSON would require explicit serialization code for every internal type. Since the cache is local and derived from trusted inputs, pickle is acceptable when documented.

### Option 6 — Use a single CLI command with flags

The app could have one `anagram` command with flags like `--mode check|find|sub`.

**Chosen / Rejected:** Rejected.

**Reason:** Argparse subcommands make the interface clearer: `check`, `find`, `sub`, `multi`, `group`, `bench`, and `cache` map directly to user intentions.

### Option 7 — Use a layered package with strategies, repositories, an engine, formatters, and CLI

This option separates the domain model from normalization, signatures, repository loading, caching, result formatting, and command-line dispatch.

**Chosen / Rejected:** Chosen.

**Reason:** It supports the small app’s core use case while demonstrating maintainable architecture. It also lets tests target isolated layers: normalization, signatures, engine behavior, and CLI behavior.

## Decision

The app uses a layered design centered on an `AnagramDetector` engine. Inputs are normalized through a configurable `NormalizationPipeline`, converted into hashable signatures through a selected `SignatureStrategy`, and searched through an `AnagramIndex` built from a `DictionaryRepository`.

The chosen default behavior is:

- Use an ordered normalization pipeline: case folding, whitespace stripping, punctuation stripping, diacritic folding, and non-alpha filtering.
- Use `SortedSignature` as the readable default signature strategy.
- Support `CounterSignature` and `PrimeSignature` as alternate strategies.
- Build dictionary indexes from bundled or file-based repositories.
- Cache indexes under `~/.anagram/cache` by default.
- Use `argparse` subcommands for the user interface.
- Return structured `MatchResult` objects internally.
- Format output with plain text, JSON, or CSV strategies.
- Catch application-level errors at the CLI boundary and return exit code 2.

## Rationale

The architecture keeps the core anagram definition visible: after normalization, two inputs are anagrams if their signature values match. The signature strategy is deliberately abstracted because there are multiple valid ways to express character equivalence. Sorting is readable; counter frequencies are mathematically direct; prime multiplication is a useful algorithmic experiment with known limits.

Normalization is also separated because “same letters” depends on user expectations. `Dormitory` and `Dirty room!!` should match when case, spacing, and punctuation are ignored. `café` and `face` may or may not match depending on diacritic folding. A configurable pipeline makes these choices explicit.

Dictionary search requires a different structure from pair comparison. Pair comparison only needs two normalized strings. Exact dictionary search needs a mapping from signature to words. Sub-anagram and multi-word search need frequency comparisons over candidate words. The `AnagramIndex` gives these operations a shared home.

The cache is intentionally below the repository/engine boundary. Repository identity, normalization pipeline, and signature strategy are included in cache keys, so stale indexes are avoided when the dictionary or algorithm settings change.

## Trade-offs Accepted

- **Pickle cache is trusted-local only.** The app should not load cache files from untrusted sources.
- **No automatic cache eviction.** Old cache files remain until `anagram cache clear` is run.
- **Prime strategy is not universally ideal.** It falls back for non-ASCII input and can produce very large integers.
- **Sub-anagram and multi-word search scan candidate words.** This is acceptable for the app’s scope but may not scale to very large dictionaries without additional indexing.
- **The CLI creates a detector for most commands.** This keeps dispatch simple but means configuration and repository resolution happen per invocation.
- **Bundled dictionaries are intentionally small.** They support zero-config demonstrations, not exhaustive language coverage.
- **No external NLP or dictionary service.** The app stays offline and standard-library-only at runtime.
- **No interactive shell.** The CLI is command-based rather than session-based.

## Consequences

- The app can be used as both a CLI and an importable package.
- New normalization rules can be added without changing the detector engine.
- New signature strategies can be benchmarked without rewriting command handlers.
- Dictionary sources can be swapped by implementing `DictionaryRepository`.
- Exact search is fast once an index has been built or loaded from cache.
- Tests can remain focused and fast using `InMemoryDictionaryRepository`.
- Cache behavior must be documented clearly because pickle is not a safe interchange format.
- The project demonstrates more architecture than the core algorithm strictly requires, which is appropriate for the portfolio stage but would be overkill for a one-off script.

## Superseded By

Not superseded. Future versions could replace pickle with a safer structured cache, add an eviction policy, add larger dictionary packs, or expose a documented plugin API for normalizers and signature strategies.


---

# Technical Design Document

## App 30 — Anagram Detector

**Utility Apps Group | Document 2 of 5**  
**Status: Accepted**

## Purpose & Scope

The Anagram Detector determines whether two inputs are anagrams and supports related dictionary workflows:

- Check whether two text inputs are anagrams.
- Find exact dictionary anagrams for a query.
- Find sub-anagrams that can be formed from a query’s letters.
- Find multi-word anagram combinations.
- Group words from a file or stdin into anagram groups.
- Benchmark available signature strategies.
- Inspect and clear the local dictionary index cache.

The app is intentionally implemented as a typed, layered Python package. Its runtime dependencies are standard-library only. Development dependencies include pytest, Hypothesis, Ruff, and mypy.

Out of scope:

- Online dictionary lookup.
- Automatic cache eviction.
- Cryptographic security around cache files.
- Full Unicode linguistic collation.
- Parallel search.
- Persistent user history.
- Interactive REPL mode.

## System Context

The app receives input from:

- CLI arguments.
- Optional stdin for `-` inputs.
- Optional dictionary files.
- Bundled dictionary files.
- Optional `~/.anagram/config.toml`.
- Existing cache files under the configured cache directory.

The app writes output to:

- stdout for successful command results.
- stderr for CLI/application errors.
- `~/.anagram/cache` or a configured cache directory for pickled dictionary indexes.

The package can be executed through:

```bash
anagram check listen silent
python -m anagram_detector check listen silent
```

## Component Breakdown

### `anagram_detector.__init__`

Exports the public library surface:

- `AnagramDetector`
- `AnagramIndex`
- `AnagramError`
- `DictionaryNotLoadedError`
- `InvalidInputError`
- `UnsupportedLanguageError`
- `AnagramGroup`
- `MatchResult`
- `MatchType`
- `Word`

This lets callers import the app’s core objects without depending on CLI internals.

### `anagram_detector.models`

Defines frozen domain data:

- `MatchType`: enum for exact, subset, superset, and partial match categories.
- `Word`: original word, normalized word, and hashable signature.
- `AnagramGroup`: group of words sharing one signature.
- `MatchResult`: structured return object for all detector operations.

`MatchResult` acts as a common response contract across check, find, sub, multi, and group operations.

### `anagram_detector.errors`

Defines application-level exceptions:

- `AnagramError`
- `InvalidInputError`
- `DictionaryNotLoadedError`
- `UnsupportedLanguageError`

The CLI catches `AnagramError` and exits with code 2.

### `anagram_detector.normalization`

Defines composable input normalization:

- `CaseFolder`
- `WhitespaceStripper`
- `PunctuationStripper`
- `DiacriticFolder`
- `NonAlphaStripper`
- `NormalizationPipeline`
- `default_pipeline`
- `pipeline_from_names`

The default pipeline case-folds text, removes whitespace, removes ASCII punctuation, strips diacritics, and drops non-alpha characters.

### `anagram_detector.signatures`

Defines interchangeable signature strategies:

- `SortedSignature`: sorted-character string baseline.
- `CounterSignature`: hashable character frequency representation.
- `PrimeSignature`: prime product for ASCII letters with fallback for non-ASCII.
- `strategy_from_name`
- `available_strategy_names`

Signatures are hashable because the index uses them as dictionary keys.

### `anagram_detector.repositories`

Defines dictionary sources:

- `DictionaryRepository`: abstract base class.
- `FileDictionaryRepository`: streams words from a local file.
- `BundledDictionaryRepository`: loads packaged dictionaries by language code.
- `InMemoryDictionaryRepository`: supports tests and embedded use.

Repositories normalize raw words and create `Word` objects using the chosen pipeline and strategy.

### `anagram_detector.cache`

Defines cache utilities:

- `default_cache_dir`
- `stable_hash`
- `file_content_hash`
- `disk_cached`
- `cache_info`
- `clear_cache`

`disk_cached` wraps pure functions and stores their output as pickle files. The index cache path is based on dictionary identity, normalization pipeline, and signature strategy.

### `anagram_detector.config`

Loads optional TOML configuration from `~/.anagram/config.toml`.

Config fields:

- `language`
- `strategy`
- `output_format`
- `cache_dir`
- `normalizers`

CLI flags override config values.

### `anagram_detector.engine`

Contains the core application logic.

`AnagramIndex` stores:

- `groups: dict[Hashable, frozenset[Word]]`
- `words: tuple[Word, ...]`

`AnagramDetector` exposes:

- `check(first, second)`
- `find_exact(query)`
- `find_subanagrams(query)`
- `find_multi_word(query, max_words, max_results)`
- `group_words(words)`

The engine normalizes inputs, validates that normalized inputs are non-empty, applies the chosen signature strategy, uses cached indexes for dictionary operations, and returns `MatchResult`.

### `anagram_detector.formatters`

Defines output strategy classes:

- `PlainFormatter`
- `JSONFormatter`
- `CSVFormatter`
- `formatter_from_name`

Formatting remains separate from detection so library callers can use structured results without parsing CLI output.

### `anagram_detector.colors`

Provides a small ANSI helper:

- `Ansi`
- `color_enabled`
- `paint`

Color is disabled when `--no-color` is passed, when `NO_COLOR` is set, or when stdout is not a TTY.

### `anagram_detector.cli`

Builds the argparse interface and dispatches commands.

Responsibilities:

- Load config.
- Parse global flags and subcommands.
- Build normalization pipeline.
- Build signature strategy.
- Build dictionary repository.
- Build detector.
- Format results.
- Catch expected errors.
- Return process-style exit codes.

### `anagram_detector.__main__`

Calls `cli.main()` so the package can run with:

```bash
python -m anagram_detector
```

## Module Dependency Graph

```text
CLI
 ├── config
 ├── cache
 ├── engine
 │    ├── cache
 │    ├── errors
 │    ├── models
 │    ├── normalization
 │    ├── repositories
 │    └── signatures
 ├── formatters
 │    ├── colors
 │    └── models
 ├── normalization
 ├── repositories
 │    ├── cache
 │    ├── errors
 │    ├── models
 │    ├── normalization
 │    └── signatures
 └── signatures

__main__
 └── cli

__init__
 ├── engine
 ├── errors
 └── models
```

## Core Algorithms & Logic

### Input normalization

Each input string passes through an ordered pipeline. The default sequence is:

1. Case-fold text.
2. Remove whitespace.
3. Remove ASCII punctuation.
4. Decompose Unicode and remove combining marks.
5. Remove non-alphabetic characters.

Example:

```text
"Dirty room!!" -> "dirtyroom"
"CAFÉ" -> "cafe"
"a b\tc\n1!" -> "abc"
```

The normalized text becomes the only input to signature generation. If the normalized text is empty, the detector raises `InvalidInputError`.

### Pair check

For `anagram check FIRST SECOND`:

1. Normalize `FIRST`.
2. Normalize `SECOND`.
3. Compute signature for both normalized strings.
4. Compare signatures.
5. Return `MatchResult` with `is_match=True` or `False`.

The algorithm is independent of dictionary loading. It does not need the `AnagramIndex`.

### Sorted signature

`SortedSignature` returns the sorted character sequence:

```text
"listen" -> "eilnst"
"silent" -> "eilnst"
```

Complexity is `O(n log n)` for input length `n`.

### Counter signature

`CounterSignature` converts a character frequency map into a hashable frozenset:

```text
"listen" -> frozenset({("l", 1), ("i", 1), ("s", 1), ("t", 1), ("e", 1), ("n", 1)})
```

This is closer to the formal definition of an anagram: identical character frequencies.

### Prime signature

`PrimeSignature` maps ASCII letters `a-z` to prime numbers and multiplies them. Anagrams have the same product because multiplication is commutative.

For non-ASCII letters, it falls back to a tagged sorted signature:

```text
("prime-fallback", sorted_signature)
```

This avoids silently ignoring unsupported characters.

### Index building

`AnagramIndex.build(words)`:

1. Deduplicates `Word` objects while preserving order.
2. Groups words by signature.
3. Stores the complete unique word tuple.
4. Stores the signature-to-group dictionary.

This supports exact lookup in `O(1)` dictionary time after the index exists.

### Exact dictionary search

`find_exact(query)`:

1. Normalize query.
2. Compute query signature.
3. Load or build index lazily.
4. Return words in the matching signature group.
5. Filter by `min_length`.

### Sub-anagram search

`find_subanagrams(query)`:

1. Normalize query.
2. Build a `Counter` of available characters.
3. Iterate indexed words.
4. Skip words shorter than `min_length` or longer than the query.
5. Include words whose character counts are contained within the query counts.
6. Sort results by normalized length and original word.

This finds words that can be formed from the query’s letters without requiring all letters to be used.

### Multi-word search

`find_multi_word(query, max_words, max_results)`:

1. Normalize query.
2. Build a target `Counter`.
3. Filter candidate words whose counters are subsets of the target.
4. Sort candidates for deterministic traversal.
5. Use recursive backtracking.
6. Track remaining letters.
7. Prevent duplicate combinations with a `seen` set.
8. Stop at `max_results`.
9. Memoize dead states to avoid repeated failed branches.

This is the most computationally expensive part of the app.

### Grouping arbitrary words

`group_words(words)`:

1. Stream input lines.
2. Strip each line.
3. Normalize each word.
4. Skip empty or too-short values.
5. Group by signature.
6. Return only groups with at least two words.

This command does not require a dictionary repository index because the input itself is the dataset.

### Disk-cached index loading

The detector index is loaded lazily through `_load_index`, wrapped by `disk_cached`.

Cache key inputs:

- Repository content identity.
- Normalization pipeline cache key.
- Signature strategy name.
- Cache directory.

The cache file name uses a SHA-256 stable hash and the `index-<hash>.pickle` naming convention.

## Data Structures

### `Word`

```python
@dataclass(frozen=True, slots=True)
class Word:
    original: str
    normalized: str
    signature: Hashable
```

Purpose:

- Preserve display text.
- Store normalized search text.
- Store hashable anagram signature.

### `AnagramGroup`

```python
@dataclass(frozen=True, slots=True)
class AnagramGroup:
    signature: Hashable
    words: frozenset[Word]
```

Purpose:

- Represent one equivalence class of anagrams.

### `MatchResult`

```python
@dataclass(frozen=True, slots=True)
class MatchResult:
    query: str
    match_type: MatchType
    matches: tuple[Word, ...]
    total_candidates_searched: int
    elapsed_ms: float
    compared_to: str | None
    is_match: bool | None
    groups: tuple[AnagramGroup, ...]
    multi_word_matches: tuple[tuple[Word, ...], ...]
```

Purpose:

- Provide one result shape for multiple commands.

### `AnagramIndex`

```python
@dataclass(frozen=True, slots=True)
class AnagramIndex:
    groups: dict[Hashable, frozenset[Word]]
    words: tuple[Word, ...]
```

Purpose:

- Fast exact lookup by signature.
- Full word iteration for sub/multi search.

### `Config`

```python
@dataclass(frozen=True, slots=True)
class Config:
    language: str
    strategy: str
    output_format: str
    cache_dir: Path
    normalizers: tuple[str, ...]
```

Purpose:

- Store configuration resolved from TOML defaults.

## State Management

The app has no long-running daemon state. Runtime state exists in four forms:

1. **Configuration state** loaded from `~/.anagram/config.toml`.
2. **Detector object state** containing repository, pipeline, strategy, cache directory, minimum length, and lazy `_index`.
3. **Index cache state** stored as pickle files under the cache directory.
4. **Process input/output state** through stdin, stdout, and stderr.

`AnagramDetector.index` is lazy. It builds or loads the index only when a command needs dictionary lookup.

## Error Handling Strategy

### Domain/application errors

The app defines a root `AnagramError` and specific subclasses:

- `InvalidInputError`
- `DictionaryNotLoadedError`
- `UnsupportedLanguageError`

The CLI catches `AnagramError`, prints a message prefixed with `anagram:`, and returns exit code 2.

### File errors

`FileNotFoundError` is caught in the CLI and reported as:

```text
anagram: file not found: <filename>
```

### Configuration and strategy errors

Unknown strategies, unknown normalizers, invalid numeric arguments, and unsupported languages are surfaced as user-facing errors.

### Argparse validation errors

Invalid command shape or invalid integer bounds are handled by argparse. The app defines `_int_at_least` to reject values such as:

```bash
anagram --min-length 0 find listen
anagram multi listen --max-words 1
```

### Empty normalized input

If an input normalizes to an empty string, the engine raises `InvalidInputError`.

Examples:

```bash
anagram check "123!!!" "???"
```

## External Dependencies

### Runtime

No third-party runtime dependencies are required. The package uses the Python standard library.

Important standard library modules include:

| Module | Use |
|---|---|
| `argparse` | CLI parsing |
| `collections.Counter` | Frequency comparisons |
| `collections.defaultdict` | Index grouping |
| `dataclasses` | Domain objects |
| `enum` | Match type enum |
| `functools.lru_cache` | Normalization/signature caching |
| `hashlib` | Stable SHA-256 hashes |
| `importlib.resources` | Bundled dictionaries |
| `pathlib` | File paths |
| `pickle` | Local disk cache |
| `tomllib` | Config parsing |
| `unicodedata` | Diacritic folding |
| `csv`, `json` | Output formatting |

### Development

Development dependencies:

| Dependency | Version constraint | Purpose |
|---|---:|---|
| `pytest` | `>=8` | Tests |
| `hypothesis` | `>=6` | Property-based testing |
| `ruff` | `>=0.6` | Linting/format checks |
| `mypy` | `>=1.10` | Strict type checking |

## Concurrency Model

The app is single-threaded and synchronous.

- Dictionary files are streamed synchronously.
- Index building is synchronous.
- Cache reads/writes are synchronous.
- Multi-word search is recursive and single-process.
- No async APIs, background workers, or locks are used.

The cache write path writes a temporary pickle and then replaces the target file. This reduces the chance of partial cache files during normal operation, but the app does not implement cross-process file locking.

## Known Limitations

- Pickle cache files are only safe for trusted local use.
- Cache files are not automatically evicted.
- Multi-word search can grow quickly with dictionary size and query length.
- Sub-anagram search scans indexed words rather than using a specialized subset index.
- Bundled dictionaries are small and meant for demonstration.
- Punctuation stripping uses ASCII punctuation before broader non-alpha stripping.
- The prime strategy is mainly educational and has practical limits.
- The app does not provide a plugin loading system for external strategies.
- The app does not expose a machine-readable error schema.
- Language support is limited to available bundled dictionary files or user-provided files.

## Design Patterns Used

- **Strategy Pattern**: normalizers, signature strategies, and output formatters.
- **Repository Pattern**: bundled, file-based, and in-memory dictionary repositories.
- **Lazy Initialization**: detector index is built only when needed.
- **Decorator Pattern**: `disk_cached` wraps index loading.
- **Value Objects**: frozen `Word`, `AnagramGroup`, and `MatchResult`.
- **Factory Function**: `strategy_from_name`, `formatter_from_name`, and `pipeline_from_names`.
- **Command Dispatcher**: CLI dispatches subcommands to engine methods.
- **Adapter Boundary**: CLI converts arguments into repository/strategy/pipeline objects.
- **Cache Key Composition**: dictionary content, pipeline, and strategy determine cache identity.


---

# Interface Design Specification

## App 30 — Anagram Detector

**Utility Apps Group | Document 3 of 5**  
**Status: Accepted**

## Invocation Syntax

Installed console script:

```bash
anagram [GLOBAL OPTIONS] COMMAND [COMMAND OPTIONS]
```

Source-tree module execution:

```bash
PYTHONPATH=src python -m anagram_detector [GLOBAL OPTIONS] COMMAND [COMMAND OPTIONS]
```

Examples:

```bash
anagram check listen silent
anagram find listen
anagram sub listen --min-length 2
anagram multi conversation --max-words 3
anagram group words.txt
cat words.txt | anagram group -
anagram --format json find café
anagram --language fr find café
anagram bench
anagram cache info
anagram cache clear
```

## Global Argument Reference

| Name | Type | Required | Default | Accepted Values | Description |
|---|---|---:|---|---|---|
| `--language` | string | No | Config or `en` | Bundled language code such as `en`, `es`, `fr` | Select bundled dictionary language when `--dictionary` is not used. |
| `--dictionary` | path | No | None | Existing readable text file | Use a custom dictionary file instead of a bundled dictionary. |
| `--strategy` | string | No | Config or `sorted` | `sorted`, `counter`, `prime` | Select signature strategy. |
| `--no-diacritics` | flag | No | False | Present/absent | Disable diacritic folding by removing `diacritics` from the configured pipeline. |
| `--min-length` | integer | No | `1` | `>= 1` | Minimum normalized word length for dictionary results. |
| `--format` | string | No | Config or `plain` | `plain`, `json`, `csv` | Select output format. |
| `--no-color` | flag | No | False | Present/absent | Disable ANSI color in plain output. |
| `--cache-dir` | path | No | Config or `~/.anagram/cache` | Writable directory | Hidden/internal option for selecting cache directory. |

## Command Reference

### `check`

Checks whether two inputs are anagrams.

```bash
anagram check FIRST SECOND
```

| Name | Type | Required | Default | Accepted Values | Description |
|---|---|---:|---|---|---|
| `FIRST` | string | Yes | None | Any text or `-` | First input. `-` reads stdin. |
| `SECOND` | string | Yes | None | Any text or `-` | Second input. `-` reads stdin. |

### `find`

Finds exact dictionary anagrams.

```bash
anagram find TEXT
```

| Name | Type | Required | Default | Accepted Values | Description |
|---|---|---:|---|---|---|
| `TEXT` | string | Yes | None | Any text or `-` | Query text. `-` reads stdin. |

### `sub`

Finds dictionary words that can be formed from the query letters.

```bash
anagram sub TEXT
```

| Name | Type | Required | Default | Accepted Values | Description |
|---|---|---:|---|---|---|
| `TEXT` | string | Yes | None | Any text or `-` | Query text. `-` reads stdin. |

### `multi`

Finds multi-word anagram combinations.

```bash
anagram multi TEXT [--max-words N] [--max-results N]
```

| Name | Type | Required | Default | Accepted Values | Description |
|---|---|---:|---|---|---|
| `TEXT` | string | Yes | None | Any text or `-` | Query text. `-` reads stdin. |
| `--max-words` | integer | No | `3` | `>= 2` | Maximum number of words in a combination. |
| `--max-results` | integer | No | `100` | `>= 1` | Maximum combinations to return. |

### `group`

Groups words from a file or stdin into anagram groups.

```bash
anagram group SOURCE
```

| Name | Type | Required | Default | Accepted Values | Description |
|---|---|---:|---|---|---|
| `SOURCE` | path or `-` | Yes | None | Readable text file or `-` | Source of newline-separated words. `-` reads stdin. |

### `bench`

Benchmarks all signature strategies against the selected dictionary.

```bash
anagram bench
```

No command-specific arguments.

### `cache`

Manages the disk cache.

```bash
anagram cache info
anagram cache clear
```

| Name | Type | Required | Default | Accepted Values | Description |
|---|---|---:|---|---|---|
| `info` | subcommand | Yes | None | `info` | Show number and total size of cache files. |
| `clear` | subcommand | Yes | None | `clear` | Remove cached items. |

## Input Contract

### Text inputs

Text inputs may include:

- Uppercase or lowercase letters.
- Spaces.
- ASCII punctuation.
- Diacritics.
- Non-letter characters.

The default normalization pipeline strips or folds these inputs into alphabetic normalized text.

### Dictionary files

Dictionary files must be UTF-8 text files containing one word or phrase per line. Blank lines are skipped. Lines that normalize to empty strings are skipped.

### Stdin

Commands accepting `-` read from stdin:

- `check`
- `find`
- `sub`
- `multi`
- `group`

`group -` treats stdin as newline-separated words.

### Config file

Optional path:

```text
~/.anagram/config.toml
```

Supported fields:

```toml
language = "en"
strategy = "sorted"
format = "plain"
cache_dir = "~/.anagram/cache"
normalizers = ["casefold", "whitespace", "punctuation", "diacritics", "nonalpha"]
```

Precedence:

1. CLI flags.
2. Config file.
3. Hardcoded defaults.

## Output Contract

### Plain output

`check` prints:

```text
true
```

or:

```text
false
```

`find` and `sub` print one word per line, or:

```text
No matches found.
```

`multi` prints one combination per line.

`group` prints each group as:

```text
<signature>: word1 word2 word3
```

`cache info` prints:

```text
N files, B bytes
```

`cache clear` prints:

```text
Removed N cached item(s).
```

### JSON output

JSON output contains fields from `MatchResult`, including:

- `query`
- `match_type`
- `matches`
- `multi_word_matches`
- `groups`
- `compared_to`
- `is_match`
- `total_candidates_searched`
- `elapsed_ms`

Example shape:

```json
{
  "query": "listen",
  "match_type": "exact",
  "matches": [
    {
      "original": "listen",
      "normalized": "listen",
      "signature": "eilnst"
    }
  ],
  "multi_word_matches": [],
  "groups": [],
  "compared_to": null,
  "is_match": null,
  "total_candidates_searched": 1,
  "elapsed_ms": 0.123
}
```

### CSV output

CSV output varies by result type:

- `check`: `query,compared_to,is_match,elapsed_ms`
- `group`: `signature,words`
- `multi`: `query,words`
- normal matches: `query,match_type,word,normalized`

## Exit Code Reference

| Code | Meaning |
|---:|---|
| `0` | Command completed successfully. |
| `2` | Application-level error, invalid input, missing file, invalid strategy/normalizer, unsupported language, or argparse usage error. |
| Other | Unexpected Python/runtime failure outside documented behavior. |

## Error Output Behavior

Application errors are printed to stderr with an `anagram:` prefix.

Examples:

```text
anagram: Input must contain at least one alphabetic character after normalization.
anagram: No bundled dictionary exists for language 'xx'.
anagram: file not found: missing.txt
```

Argparse validation errors also print usage text and an error message to stderr.

## Environment Variables

| Name | Required | Default | Description |
|---|---:|---|---|
| `NO_COLOR` | No | unset | Disables ANSI color in plain output when present. |
| `PYTHONPATH` | No | install-dependent | Can be set to `src` when running without installation. |

## Configuration Files

### `~/.anagram/config.toml`

Optional user config.

Example:

```toml
language = "en"
strategy = "sorted"
format = "plain"
cache_dir = "~/.anagram/cache"
normalizers = ["casefold", "whitespace", "punctuation", "diacritics", "nonalpha"]
```

Invalid normalizer names cause a `ValueError`.

Unknown strategies cause a `ValueError`.

Unsupported bundled languages cause `UnsupportedLanguageError`.

## Side Effects

| Operation | Side Effect |
|---|---|
| `find`, `sub`, `multi`, `bench` | May read bundled or custom dictionary file. |
| `find`, `sub`, `multi` | May create cache directory and pickle index file. |
| `cache info` | Reads cache directory metadata. |
| `cache clear` | Deletes cache directory contents and recreates the directory. |
| `group FILE` | Reads a user-provided file. |
| `group -` | Reads stdin. |

`check` does not require dictionary loading and normally has no filesystem side effects unless config loading is considered.

## Usage Examples

### Basic check

```bash
anagram check listen silent
```

Expected output:

```text
true
```

### Phrase with punctuation and spaces

```bash
anagram check "Dormitory" "Dirty room!!"
```

Expected output:

```text
true
```

### JSON exact search

```bash
anagram --format json find listen
```

Expected output shape:

```json
{
  "query": "listen",
  "match_type": "exact",
  "matches": []
}
```

The actual `matches` array depends on the selected dictionary.

### Sub-anagrams with minimum length

```bash
anagram --min-length 2 sub listen
```

Expected behavior:

- Returns dictionary words of length 2 or more that can be formed from the letters in `listen`.

### Multi-word search

```bash
anagram multi conversation --max-words 3 --max-results 25
```

Expected behavior:

- Returns up to 25 combinations of 2–3 words that use the query letters.

### Group words from stdin

```bash
printf "care\nrace\nacre\nhello\n" | anagram group -
```

Expected output includes:

```text
acer: acre care race
```

The exact signature display depends on the active strategy.

### Use French dictionary

```bash
anagram --language fr find café
```

Expected behavior:

- Loads bundled French dictionary if available.
- Applies default diacritic folding unless `--no-diacritics` is used.

### Use custom dictionary

```bash
anagram --dictionary ./words.txt find triangle
```

Expected behavior:

- Streams `./words.txt`.
- Builds or loads cache based on the file content hash.

### Cache info

```bash
anagram cache info
```

Expected output:

```text
3 files, 24871 bytes
```

### Cache clear

```bash
anagram cache clear
```

Expected output:

```text
Removed 3 cached item(s).
```

### Intentional failure: invalid minimum length

```bash
anagram --min-length 0 find listen
```

Expected behavior:

- Exits nonzero.
- Prints an argparse error mentioning `min-length must be >= 1`.

### Intentional failure: unsupported language

```bash
anagram --language xx find listen
```

Expected behavior:

```text
anagram: No bundled dictionary exists for language 'xx'.
```


---

# Runbook

## App 30 — Anagram Detector

**Utility Apps Group | Document 4 of 5**  
**Status: Accepted**

## Prerequisites

- Python 3.11 or newer.
- A shell environment capable of running Python modules or installed console scripts.
- Optional custom dictionary file for larger searches.
- Optional development tools for verification:
  - pytest
  - Hypothesis
  - Ruff
  - mypy

## Installation Procedure

### Standard editable install

```bash
python -m pip install -e .
```

Verify:

```bash
anagram --help
```

### Development install

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
```

or:

```bash
python -m pip install -e ".[dev]"
```

### Source-tree execution without install

PowerShell:

```powershell
$env:PYTHONPATH = "src"
python -m anagram_detector check listen silent
```

POSIX shell:

```bash
PYTHONPATH=src python -m anagram_detector check listen silent
```

## Configuration Steps

### Optional user config

Create:

```text
~/.anagram/config.toml
```

Example:

```toml
language = "en"
strategy = "sorted"
format = "plain"
cache_dir = "~/.anagram/cache"
normalizers = ["casefold", "whitespace", "punctuation", "diacritics", "nonalpha"]
```

### Validate basic configuration

```bash
anagram check listen silent
anagram cache info
```

### Choose a custom dictionary

```bash
anagram --dictionary ./words.txt find listen
```

### Disable color output

```bash
anagram --no-color check listen silent
```

or set:

```bash
NO_COLOR=1
```

## Standard Operating Procedures

### Check two strings

```bash
anagram check "Dormitory" "Dirty room!!"
```

Use this when the user only needs a yes/no answer.

### Find exact dictionary anagrams

```bash
anagram find listen
```

Use this when the user wants dictionary words with the same letters.

### Find sub-anagrams

```bash
anagram sub stand
```

Use this when the user wants words that can be made from a larger set of letters.

### Find multi-word anagrams

```bash
anagram multi conversation --max-words 3 --max-results 50
```

Use conservative limits when the query is long or the dictionary is large.

### Group a word file

```bash
anagram group words.txt
```

Use this to discover all anagram groups in a supplied list.

### Group words from stdin

```bash
cat words.txt | anagram group -
```

Use this in pipelines.

### Benchmark strategies

```bash
anagram bench
```

Use this to compare `sorted`, `counter`, and `prime` strategies on the active dictionary.

### Inspect cache

```bash
anagram cache info
```

### Clear cache

```bash
anagram cache clear
```

Run this if dictionary results look stale, disk usage is high, or a cache file may be corrupted.

## Health Checks

### CLI available

```bash
anagram --help
```

Expected:

- Usage text prints.
- Exit code 0.

### Pair comparison works

```bash
anagram check listen silent
```

Expected:

```text
true
```

### Normalization works

```bash
anagram check "Dormitory" "Dirty room!!"
```

Expected:

```text
true
```

### JSON output works

```bash
anagram --format json check listen silent
```

Expected:

- Valid JSON.
- `is_match` is `true`.

### Bundled dictionary loads

```bash
anagram find listen
```

Expected:

- Exit code 0.
- Either matching words or `No matches found.`
- Cache may be created on first run.

### Cache management works

```bash
anagram cache info
```

Expected:

```text
N files, B bytes
```

## Expected Output Samples

### `check`

Command:

```bash
anagram check listen silent
```

Output:

```text
true
```

### `find`

Command:

```bash
anagram find listen
```

Possible output:

```text
enlist
listen
silent
```

Actual output depends on the active dictionary.

### `group`

Input file:

```text
care
race
acre
hello
```

Command:

```bash
anagram group words.txt
```

Possible output:

```text
acer: acre care race
```

### `bench`

Command:

```bash
anagram bench
```

Output shape:

```text
words,123
sorted,0.421
counter,0.816
prime,0.388
```

Actual timing depends on hardware and dictionary size.

## Known Failure Modes

### Unsupported language

Cause:

```bash
anagram --language xx find listen
```

Symptom:

```text
anagram: No bundled dictionary exists for language 'xx'.
```

Resolution:

- Use a supported bundled language.
- Pass `--dictionary PATH`.
- Update config `language`.

### Missing dictionary file

Cause:

```bash
anagram --dictionary missing.txt find listen
```

Symptom:

```text
anagram: file not found: missing.txt
```

Resolution:

- Verify path.
- Use an absolute path.
- Check file permissions.

### Invalid normalizer name

Cause:

```toml
normalizers = ["casefold", "typo-normalizer"]
```

Symptom:

```text
anagram: Unknown normalizer(s): typo-normalizer.
```

Resolution:

- Use only `casefold`, `whitespace`, `punctuation`, `diacritics`, and `nonalpha`.

### Invalid strategy

Cause:

```toml
strategy = "frequency"
```

Symptom:

```text
anagram: Unknown strategy 'frequency'. Choose one of: counter, prime, sorted.
```

Resolution:

- Use `sorted`, `counter`, or `prime`.

### Empty normalized input

Cause:

```bash
anagram check "123!!!" "???"
```

Symptom:

```text
anagram: Input must contain at least one alphabetic character after normalization.
```

Resolution:

- Provide input containing letters.
- Modify normalizers if appropriate.

### Multi-word search is slow

Cause:

- Large dictionary.
- Long query.
- High `--max-words`.
- High `--max-results`.

Resolution:

- Lower `--max-words`.
- Lower `--max-results`.
- Raise `--min-length`.
- Use a smaller dictionary.

### Cache grows over time

Cause:

- Cache keys include dictionary content, pipeline, and strategy.
- Old cache files are not evicted automatically.

Resolution:

```bash
anagram cache clear
```

### Suspicious cache file

Cause:

- Manual edits to cache directory.
- Interrupted process.
- Untrusted cache copied from another machine.

Resolution:

```bash
anagram cache clear
```

Do not use cache files from untrusted sources.

## Troubleshooting Decision Tree

```text
Command not found?
├── Yes
│   ├── Did you install with python -m pip install -e .?
│   │   ├── No: install the package.
│   │   └── Yes: check virtual environment activation.
│   └── Use PYTHONPATH=src python -m anagram_detector as fallback.
└── No
    └── Continue.

Command exits with usage error?
├── Check command spelling.
├── Check required positional arguments.
├── Check numeric bounds for --min-length, --max-words, --max-results.
└── Re-run with --help.

No matches found?
├── Is the active dictionary correct?
├── Did normalization remove expected characters?
├── Try --format json to inspect normalized output in matches.
├── Try a known example like listen/silent.
└── Try a custom dictionary.

Search is slow?
├── Is the dictionary large?
├── Is this the first run before cache exists?
├── Lower --max-results.
├── Lower --max-words.
├── Increase --min-length.
└── Use cache info to confirm index reuse.

Cache error or suspicious cache?
├── Run anagram cache clear.
├── Re-run the command.
└── Avoid untrusted cache files.
```

## Dependency Failure Handling

### Python version too old

Symptom:

- Installation or syntax errors.
- `tomllib` missing in older versions.

Resolution:

- Use Python 3.11+.

### Missing dev dependencies

Symptom:

```text
No module named pytest
```

Resolution:

```bash
python -m pip install -e ".[dev]"
```

### Editable install path issue

Symptom:

- `anagram` command not found.
- Package import failure.

Resolution:

```bash
python -m pip install -e .
python -c "import anagram_detector; print(anagram_detector.__all__)"
```

### Broken custom dictionary encoding

Symptom:

- Unicode decode error reading file.

Resolution:

- Save dictionary as UTF-8.
- Remove invalid byte sequences.

## Recovery Procedures

### Clear and rebuild cache

```bash
anagram cache clear
anagram find listen
```

### Reset config to defaults

```bash
mv ~/.anagram/config.toml ~/.anagram/config.toml.bak
anagram check listen silent
```

### Use a temporary cache directory

```bash
anagram --cache-dir ./tmp-cache find listen
```

### Verify source execution

```bash
PYTHONPATH=src python -m anagram_detector check listen silent
```

### Reinstall package

```bash
python -m pip uninstall anagram-detector
python -m pip install -e .
```

## Logging Reference

The app does not implement a dedicated logging subsystem. Operational feedback is through:

- stdout for normal command results.
- stderr for errors.
- cache files under the configured cache directory.

For debugging, use:

```bash
anagram --format json find listen
anagram cache info
```

## Maintenance Notes

- Keep bundled dictionaries small enough for quick zero-config demos.
- Do not commit local cache files.
- Document any new normalizer name in README/config examples.
- Add tests for every new signature strategy.
- Add tests for every new CLI command or argument validation path.
- Treat pickle cache as implementation detail, not a portable file format.
- If cache schema changes, update cache key composition.
- Keep runtime dependencies at zero unless a dependency provides clear value.
- Prefer deterministic output ordering in tests and docs.


---

# Lessons Learned

## App 30 — Anagram Detector

**Utility Apps Group | Document 5 of 5**  
**Status: Accepted**

## Project Summary

Anagram Detector started from a classic beginner exercise: compare two strings and determine if they are anagrams. The final version grew into a small but layered CLI application with a reusable detection engine, typed domain models, configurable normalization, multiple signature strategies, dictionary repositories, disk-cached indexes, multiple search modes, output formatting strategies, and tests across core logic and CLI behavior.

The project demonstrates how a simple algorithm can be turned into a maintainable utility without losing sight of the original problem. The core idea remains straightforward: normalize text, compute a signature, compare or group by that signature.

## Original Goals vs. Actual Outcome

### Original goals

- Build a CLI that determines whether two strings are anagrams.
- Use character frequency comparison rather than a fragile string-only approach.
- Ignore differences like case and spacing where appropriate.
- Keep the project small and readable.
- Practice tests and command-line behavior.

### Actual outcome

The app now supports:

- Pair checking.
- Exact dictionary search.
- Sub-anagram search.
- Multi-word anagram search.
- Grouping from files or stdin.
- Bundled dictionaries.
- Custom dictionary files.
- Disk-cached indexes.
- Multiple signature strategies.
- Configurable normalization.
- Plain, JSON, and CSV output.
- Cache management commands.
- Tests for normalization, signatures, engine behavior, and CLI behavior.

The outcome is larger than the smallest possible solution, but the extra complexity is tied to clear learning goals.

## Technical Decisions That Paid Off

### Separating normalization from detection

Normalization is not an implementation detail; it defines what the app considers “the same letters.” Moving it into its own pipeline made the behavior explicit and configurable.

This paid off immediately for examples like:

```text
Dormitory
Dirty room!!
```

It also made diacritic behavior testable.

### Using signature strategies

The app can compare sorted strings, counter frequencies, or prime products using the same detector interface. This makes algorithm trade-offs visible.

The strategy pattern also avoids hard-coding one “correct” method. For a learning project, this is valuable because each strategy teaches something different.

### Keeping `MatchResult` structured

Returning structured domain results instead of formatted strings keeps the engine reusable. The CLI can render plain text, JSON, or CSV without changing the core algorithm.

### Repository abstraction for dictionaries

A dictionary may come from:

- A bundled package file.
- A user-supplied file.
- An in-memory list during tests.

The repository boundary prevents the engine from caring where words come from.

### Disk-cached indexes

Caching makes repeated dictionary searches more practical. The cache key includes the dictionary identity, normalization pipeline, and signature strategy, which prevents many stale-cache bugs.

### Argparse subcommands

The CLI is easier to use because each operation has a command name:

```bash
anagram check
anagram find
anagram sub
anagram multi
anagram group
anagram bench
anagram cache
```

This is clearer than a single command with a `--mode` flag.

## Technical Decisions That Created Debt

### Pickle cache format

Pickle is convenient but not safe for untrusted files. This is acceptable for a local derived cache, but it creates a documentation and trust-boundary requirement.

A future version could use SQLite or a JSON-lines cache format if portability and safety become more important.

### Multi-word search complexity

Recursive search is understandable and works for this scope, but multi-word anagram search can become expensive quickly. The current controls help:

- `--max-words`
- `--max-results`
- `--min-length`
- candidate filtering
- dead-state memoization

Still, this is the area most likely to need optimization.

### No cache eviction

The cache is simple and predictable, but it can grow over time. The user must run:

```bash
anagram cache clear
```

This is acceptable for a portfolio CLI but would need an eviction policy in a long-lived production utility.

### Config validation is minimal

The config loader reads TOML and converts fields, but most validation happens later when strategies, normalizers, and repositories are built. This keeps the loader simple but means errors may appear during command dispatch.

### Superset match type is modeled but not implemented as a command

`MatchType` includes `SUPERSET`, but the CLI does not expose a dedicated superset command. This is a small domain/API mismatch. It may be a placeholder for future expansion, but it should either be implemented or removed later.

## What Was Harder Than Expected

### Defining “same letters”

At first, an anagram sounds like a simple frequency problem. In practice, user expectations require decisions:

- Should spaces count?
- Should punctuation count?
- Should case count?
- Should accents count?
- Should numbers count?
- Should non-English letters count?

The normalization pipeline became necessary because these are product decisions, not just algorithm decisions.

### Multi-word anagram search

Exact anagram search is simple once signatures exist. Multi-word search is harder because it becomes a combinatorial search problem. Candidate filtering and dead-state memoization help, but the complexity is still much higher than pair checking.

### Caching without stale results

A cache is only useful if it invalidates when inputs change. The app had to include dictionary content, normalization settings, and signature strategy in the cache key. Using only the dictionary path would have been incorrect.

### Keeping CLI and engine separate

It is tempting to build everything inside command handlers. Separating CLI construction from engine behavior required more modules, but it made the project easier to test and explain.

## What Was Easier Than Expected

### Exact matching with signatures

Once normalization was solved, exact anagram detection became simple. Any hashable representation shared by anagrams can power the comparison and the index.

### Adding JSON and CSV output

Because the engine returns `MatchResult`, formatters could be added without changing detection logic.

### Testing with in-memory dictionaries

`InMemoryDictionaryRepository` made the core engine testable without relying on bundled files or filesystem setup.

### Supporting stdin

The `-` convention is simple and powerful. It lets `group` work naturally in shell pipelines.

## Python-Specific Learnings

### `collections.Counter`

`Counter` is a natural fit for frequency comparison. It also supports subtraction and membership-style reasoning for sub-anagram checks.

### Frozen dataclasses with slots

`Word`, `AnagramGroup`, and `MatchResult` are small data carriers. Frozen dataclasses make them predictable, while slots reduce accidental attribute creation.

### Protocols

Protocols are useful for strategy and formatter interfaces. They allow duck typing while keeping the design explicit for type checking.

### `importlib.resources`

Bundled data files should not be addressed with fragile relative paths. `importlib.resources` is the right tool for package data.

### `functools.lru_cache`

Caching normalized strings and signature computations is simple and effective for repeated inputs.

### `pathlib`

Path handling is clearer with `Path`, especially for config paths, dictionary paths, and cache directories.

### `argparse`

Argparse subcommands can support a surprisingly rich CLI without third-party dependencies.

### `tomllib`

Python 3.11’s built-in TOML reader makes small configuration files easy without adding runtime dependencies.

## Architecture Insights

### A simple algorithm can still have multiple boundaries

The core anagram comparison is small. The application around it has multiple real boundaries:

- Input normalization.
- Signature generation.
- Dictionary source.
- Index building.
- Cache persistence.
- Search mode.
- Output format.
- CLI error handling.

Naming these boundaries made the project more maintainable.

### Strategies are useful when behavior is genuinely interchangeable

The signature strategy abstraction is justified because all strategies answer the same question: “what hashable value represents this normalized text’s letters?”

The normalizer strategy abstraction is also justified because each normalizer is a small, independent transformation.

### Caching belongs below the public query API

Users should not need to know when an index is cached. The detector loads the index lazily and the cache wrapper handles persistence. This keeps the public API clean.

### CLI output should be a final step

The CLI should not be the source of truth. Structured result objects make it easy to support multiple formats and tests.

## Testing Gaps

The existing tests cover major areas:

- Engine pair checking.
- Exact search.
- Sub-anagrams.
- Multi-word detection.
- Grouping.
- Normalization behavior.
- Signature agreement and non-anagram rejection.
- Prime fallback for non-ASCII.
- CLI check command.
- CLI JSON find.
- CLI group from stdin.
- CLI argument validation for minimum length and max words.

Remaining gaps to consider:

- Cache corruption behavior.
- Cache invalidation when dictionary content changes.
- `cache info` and `cache clear` CLI behavior.
- Custom config file loading.
- Unknown normalizer and unknown strategy errors from CLI.
- Unsupported bundled language behavior.
- CSV formatter output for each result type.
- File dictionary repository with temporary files.
- Very long query inputs.
- Unicode edge cases beyond simple diacritics.
- Multi-word search duplicate prevention under larger dictionaries.

## Reusable Patterns Identified

- **Normalize, then operate**: define input cleanup once and reuse everywhere.
- **Hashable signature as equivalence class**: useful for anagrams and other grouping problems.
- **Repository interface for data sources**: bundled, file, and memory-backed data can share one API.
- **Structured result plus formatter**: avoids mixing business logic with display logic.
- **Cache identity from all semantic inputs**: include content and algorithm settings, not just file paths.
- **CLI subcommands as use-case boundaries**: each command maps to one application behavior.
- **In-memory repository for tests**: fast tests without filesystem dependency.
- **Local cache management command**: any persistent cache should have at least an inspect and clear operation.

## If I Built This Again

I would keep the layered architecture, but I would make several improvements:

1. Add a dedicated `cache` test module.
2. Add config validation before command dispatch.
3. Add a safer cache format or versioned cache metadata.
4. Add an optional maximum dictionary size warning for multi-word searches.
5. Add a `--explain` flag showing normalization and signatures for debugging.
6. Add a `superset` command or remove the unused enum value.
7. Add a documented performance note for each signature strategy.
8. Add larger optional dictionaries outside the base package.
9. Add a direct library example to the README.
10. Add command examples for CSV output.

## Open Questions

- Should diacritic folding be enabled by default for every language?
- Should `prime` remain available as a normal strategy or only as a benchmark/demo?
- Should cache files include a version header?
- Should cache files expire automatically?
- Should multi-word search return only exact full-letter matches, or should partial phrase matches be a separate command?
- Should dictionary results exclude the query word itself by default?
- Should the app support phrase dictionaries?
- Should config loading validate all fields before dispatch?
- Should output include normalized query and active strategy in plain mode when requested?
- Should `DictionaryNotLoadedError` remain in the public API if the detector lazily loads the index automatically?
