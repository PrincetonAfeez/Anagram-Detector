"""Custom exception hierarchy for the anagram detector."""


class AnagramError(Exception):
    """Base class for all application-level errors."""


class InvalidInputError(AnagramError):
    """Raised when user input normalizes to an empty value or is otherwise invalid."""


class DictionaryNotLoadedError(AnagramError):
    """Raised when a query is attempted before the dictionary index is available."""


class UnsupportedLanguageError(AnagramError):
    """Raised when no bundled dictionary exists for the requested language."""
