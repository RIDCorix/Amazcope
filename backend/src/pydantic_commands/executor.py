"""Command executor for running commands."""

import argparse
import sys

from pydantic_commands.base import BaseCommand
from pydantic_commands.registry import command_registry


class CommandExecutor:
    """
    Executor for running commands from the registry.

    This class provides the main entry point for command-line applications,
    similar to Django's execute_from_command_line.
    """

    def __init__(self, prog_name: str | None = None) -> None:
        """
        Initialize the executor.

        Args:
            prog_name: Program name for help text
        """
        self.prog_name = prog_name or sys.argv[0]

    def create_parser(self) -> argparse.ArgumentParser:
        """
        Create the main argument parser with subcommands.

        Returns:
            ArgumentParser with all registered commands as subcommands
        """
        parser = argparse.ArgumentParser(
            prog=self.prog_name,
            description="Command-line management utility",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        # Add version argument
        parser.add_argument(
            "--version",
            action="version",
            version="%(prog)s 0.1.0",
        )

        # Create subparsers for commands
        subparsers = parser.add_subparsers(
            title="Available commands",
            dest="command",
            help="Command to run",
        )

        # Register all commands as subcommands
        for command_name in command_registry.registry:
            command_instance = command_registry.get(command_name)
            command_instance.create_parser(prog_name=self.prog_name, subparsers=subparsers)

        return parser

    def execute(self, argv: list[str] | None = None) -> int:
        """
        Execute a command from command-line arguments.

        Args:
            argv: Command-line arguments (defaults to sys.argv)

        Returns:
            Exit code
        """
        if argv is None:
            argv = sys.argv[1:]

        # If no arguments, show help
        if not argv:
            argv = ["--help"]

        # Parse only the command name first (not the arguments)
        parser = self.create_parser()

        # Try to extract command name without full parsing
        command_name = None
        if argv and not argv[0].startswith("-"):
            command_name = argv[0]

        # If no command specified or help requested at top level, show main help
        if not command_name or command_name in ["--help", "-h", "help"]:
            parser.parse_args(argv)  # This will show help and exit
            return 0

        # Get the command
        try:
            command: BaseCommand = command_registry.get(command_name)
        except KeyError:
            print(f"Unknown command: {command_name}", file=sys.stderr)
            print(f"Available commands: {', '.join(command_registry.list())}")
            return 1

        # Parse command-specific arguments (skip the command name itself)
        command_argv = argv[1:] if len(argv) > 1 else []

        try:
            # Try to parse arguments (may prompt interactively if missing)
            command_args = command.parse_arguments(command_argv)
        except SystemExit as e:
            # If argparse exits (missing args), return its exit code
            return e.code if isinstance(e.code, int) else 1
        except Exception as e:
            print(f"Error parsing arguments: {e}", file=sys.stderr)
            return 1

        # Execute the command
        return command.execute(command_args)


def execute_from_command_line(argv: list[str] | None = None) -> int:
    """
    Execute a command from command-line arguments.

    This is a convenience function similar to Django's execute_from_command_line.

    Args:
        argv: Command-line arguments (defaults to sys.argv)

    Returns:
        Exit code
    """
    executor = CommandExecutor()
    return executor.execute(argv)


def host_cli(argv: list[str] | None = None, prog_name: str | None = None) -> None:
    """
    Host a CLI application with registered commands.

    This is the main entry point for CLI applications, similar to Django's manage.py.
    It automatically discovers and executes registered commands, then exits with
    the appropriate exit code.

    Usage:
        # cli.py
        from pydantic_commands import host_cli

        if __name__ == "__main__":
            host_cli()

    Then run:
        python cli.py command_name --arg1 value1 --arg2 value2

    Args:
        argv: Command-line arguments (defaults to sys.argv)
        prog_name: Program name for help text (defaults to sys.argv[0])
    """
    executor = CommandExecutor(prog_name=prog_name)
    exit_code = executor.execute(argv)
    sys.exit(exit_code)
