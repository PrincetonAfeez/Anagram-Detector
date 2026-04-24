# Architecture

## Normalization Pipeline

Normalization is a composable strategy chain. The default pipeline applies case folding,
whitespace stripping, punctuation stripping, diacritic folding, and non-alpha filtering. Each
normalizer has one job, and `NormalizationPipeline` applies them in order. This lets config or
CLI flags change the pipeline without rewriting the detector.

## Signature Strategies

The engine accepts any `SignatureStrategy`.

`SortedSignature` joins sorted letters and is the easiest to reason about. `CounterSignature`
uses a hashable frequency representation and pairs naturally with subset checks. `PrimeSignature`
maps ASCII letters to primes and multiplies them, which is a neat O(n) trick for short words, but
the product grows quickly and non-ASCII input falls back to a sorted signature.

## Indexing Vs Per-Query Work

The dictionary is indexed once into `dict[Hashable, frozenset[Word]]`. Exact anagram lookup is
then a normalization step, a signature computation, and one dictionary lookup. Subset and
multi-word searches still scan candidates, but they reuse the normalized `Word` objects produced
when the index was built.

## Cache Invalidation

The cached index key includes the dictionary identity, dictionary content hash, normalization
pipeline key, and signature strategy name. Editing a dictionary file changes the content hash,
which naturally points to a new cache file. Old cache files are not automatically evicted because
that policy is better kept explicit for a teaching project.
