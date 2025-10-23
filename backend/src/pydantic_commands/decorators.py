"""Decorators for creating commands from functions."""

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel

from pydantic_commands.base import BaseCommand
from pydantic_commands.registry import command_registry


def command(
    name: str | None = None,
    help: str | None = None,
    description: str | None = None,
    arguments: type[BaseModel] | None = None,
    register: bool = True,
) -> Callable:  # type: ignore[type-arg]
    """
    Decorator to create a command from a function.

    This decorator allows you to define commands using simple functions
    instead of classes, while still benefiting from Pydantic validation.

    Args:
        name: Command name (defaults to function name)
        help: Short help text
        description: Detailed description
        arguments: Pydantic model class for arguments
        register: Whether to automatically register the command

    Example:
        class UserArgs(BaseModel):
            username: str
            email: str
            age: int = 18

        @command(name="createuser", help="Create a user", arguments=UserArgs)
        def create_user_command(args: UserArgs) -> None:
            print(f"Creating {args.username}")
    """

    def decorator(func: Callable) -> type[BaseCommand]:  # type: ignore[type-arg]
        # Extract metadata
        cmd_name = name or func.__name__.replace("_", "-")
        cmd_help = help or func.__doc__ or ""
        cmd_description = description or cmd_help

        # Extract arguments from function signature if not provided
        cmd_arguments = arguments
        if cmd_arguments is None:
            import inspect

            sig = inspect.signature(func)
            if sig.parameters:
                # Get the first parameter's annotation
                first_param = list(sig.parameters.values())[0]
                if first_param.annotation != inspect.Parameter.empty:
                    # Check if it's a BaseModel subclass
                    if isinstance(first_param.annotation, type) and issubclass(
                        first_param.annotation, BaseModel
                    ):
                        cmd_arguments = first_param.annotation

        # Create a command class dynamically
        class DecoratedCommand(BaseCommand):  # type: ignore[type-arg]
            name = cmd_name
            help = cmd_help
            description = cmd_description
            Arguments = cmd_arguments

            def handle(self, args: Any) -> None:
                """Execute the command."""
                func(args)
                return

        # Set a better name for the class
        DecoratedCommand.__name__ = f"{func.__name__.title().replace('_', '')}Command"
        DecoratedCommand.__module__ = func.__module__

        # Register if requested
        if register:
            command_instance = DecoratedCommand()
            command_registry.register()(command_instance)
        return DecoratedCommand

    return decorator
