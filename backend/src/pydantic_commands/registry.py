"""Command registry for managing command instances."""

from __future__ import annotations

from typing import TYPE_CHECKING

from any_registries import Registry

if TYPE_CHECKING:
    from pydantic_commands.base import BaseCommand


def _get_command_name(cmd: BaseCommand) -> str:
    """Extract command name from a command instance."""
    return cmd.name or cmd.__class__.__name__.lower().replace("command", "")


# Global command registry
command_registry: Registry[str, BaseCommand] = Registry(
    key=_get_command_name,
).auto_load("*/commands.py")
