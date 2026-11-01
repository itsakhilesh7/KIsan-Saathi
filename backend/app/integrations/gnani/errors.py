"""Typed exception hierarchy for Gnani voice APIs."""


class GnaniError(Exception):
    """Base exception for all Gnani API interactions."""


class STTError(GnaniError):
    """Raised when Speech-to-Text (Prisma) fails."""


class TTSError(GnaniError):
    """Raised when Text-to-Speech (Timbre) fails."""


class GnaniRateLimitError(GnaniError):
    """Raised when HTTP 429 Too Many Requests is encountered."""
