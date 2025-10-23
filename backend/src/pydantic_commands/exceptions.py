"""Exception classes for pydantic-commands."""


class CommandError(Exception):
    """
    Exception raised when a command encounters an error during execution.

    Similar to Django's CommandError, this is used to indicate issues
    that should be reported to the user without a full traceback.
    """

    pass


class CommandNotFoundError(CommandError):
    """Exception raised when a command is not found in the registry."""

    pass


class CommandValidationError(CommandError):
    """Exception raised when command argument validation fails."""

    pass
