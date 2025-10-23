"""
Pydantic Commands - A Django-like command system with Pydantic integration.

This library provides a command framework similar to Django's management commands,
but with automatic argparse generation from Pydantic models.
"""

from pydantic_commands.base import BaseCommand, CommandError
from pydantic_commands.decorators import command
from pydantic_commands.executor import CommandExecutor, host_cli
from pydantic_commands.registry import command_registry

__version__ = "0.1.0"
__all__ = [
    "BaseCommand",
    "CommandError",
    "command",
    "CommandExecutor",
    "command_registry",
    "host_cli",
]
