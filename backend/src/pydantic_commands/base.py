"""Base command class similar to Django's BaseCommand."""

import argparse
import io
import sys
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar, get_args, get_origin

from pydantic import BaseModel, ValidationError

from pydantic_commands.exceptions import CommandValidationError
from pydantic_commands.parser import PydanticArgumentParser

ARG_TYPE = TypeVar("ARG_TYPE", bound=BaseModel)


class BaseCommand(ABC, Generic[ARG_TYPE]):
    """
    Base class for all commands.

    Similar to Django's BaseCommand, this provides the structure for
    creating command-line commands with automatic argument parsing
    from Pydantic models.

    Example:
        class UserCreateCommand(BaseCommand):
            name = "createuser"
            help = "Create a new user"

            class Arguments(BaseModel):
                username: str
                email: str
                age: int = 18

            def handle(self, args: Arguments) -> None:
                print(f"Creating user {args.username}")
    """

    # Command metadata
    name: str = ""
    help: str = ""
    description: str = ""
    epilog: str = ""

    # Argument model
    arg_type: type[ARG_TYPE] | None = None

    def __init__(self) -> None:
        """Initialize the command."""
        if not self.name:
            self.name = self.__class__.__name__.lower().replace("command", "")
        if not self.description:
            self.description = self.help

    def create_parser(
        self, prog_name: str = "", subparsers: argparse._SubParsersAction | None = None
    ) -> argparse.ArgumentParser:
        """
        Create an ArgumentParser for this command.

        Args:
            prog_name: The program name to use
            subparsers: Optional subparser action to add this command to

        Returns:
            ArgumentParser configured with this command's arguments
        """
        if subparsers:
            # Create subparser for this command
            parser = subparsers.add_parser(
                self.name,
                help=self.help,
                description=self.description or self.help,
                epilog=self.epilog,
                formatter_class=argparse.RawDescriptionHelpFormatter,
            )
        else:
            # Create standalone parser
            parser = argparse.ArgumentParser(
                prog=prog_name or self.name,
                description=self.description or self.help,
                epilog=self.epilog,
                formatter_class=argparse.RawDescriptionHelpFormatter,
            )

        # Add arguments from Pydantic model
        if hasattr(self, "Arguments") and self.Arguments is not None:
            pydantic_parser = PydanticArgumentParser(self.Arguments)
            pydantic_parser.add_arguments_to_parser(parser)

        # Allow subclasses to add custom arguments
        self.add_arguments(parser)

        return parser  # type: ignore[return-value]

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """
        Hook for subclasses to add additional arguments.

        Args:
            parser: The ArgumentParser to add arguments to
        """
        pass

    def parse_arguments(self, args: list[str]) -> Any:
        """
        Parse command-line arguments with interactive prompting for missing required fields.

        Args:
            args: List of argument strings

        Returns:
            Parsed arguments (Pydantic model instance if Arguments is defined)

        Raises:
            CommandValidationError: If argument validation fails
            SystemExit: If argparse fails and interactive mode is not available
        """
        # Check if help is requested
        if "--help" in args or "-h" in args:
            parser = self.create_parser()
            parser.parse_args(args)  # This will print help and exit
            return None

        # If we have an Arguments model, try interactive mode first
        if hasattr(self, "Arguments") and self.Arguments is not None:
            # Check if we can parse without errors
            parser = self.create_parser()

            # Suppress error messages temporarily to check if parsing will fail
            old_stderr = sys.stderr
            captured_stderr = io.StringIO()
            sys.stderr = captured_stderr

            try:
                parsed_args = parser.parse_args(args)
                # Restore stderr
                sys.stderr = old_stderr
                # Success! Convert to Pydantic model
                args_dict = vars(parsed_args)
                return self.Arguments(**args_dict)
            except SystemExit as e:
                # Restore stderr
                sys.stderr = old_stderr
                # Don't print the captured errors - we're going to interactive mode

                #  Parsing failed (missing required args)
                if e.code == 0:
                    # Help was shown, just exit
                    raise
                # Try interactive mode
                try:
                    return self._prompt_for_arguments(args)
                except (KeyboardInterrupt, EOFError):
                    print("\n\n❌ Operation cancelled by user.")
                    raise SystemExit(1) from None
            except ValidationError as e:
                # Restore stderr
                sys.stderr = old_stderr
                raise CommandValidationError(f"Argument validation failed: {e}")
        else:
            # No Arguments model, just use argparse normally
            parser = self.create_parser()
            return parser.parse_args(args)

    def _prompt_for_arguments(self, provided_args: list[str]) -> Any:
        """
        Interactively prompt for missing required arguments.

        Args:
            provided_args: Arguments already provided by the user

        Returns:
            Pydantic model instance with all required fields

        Raises:
            CommandValidationError: If validation fails after prompting
        """
        if not hasattr(self, "Arguments") or self.Arguments is None:
            return {}

        # Parse provided arguments silently (allow partial/missing required args)
        parser = argparse.ArgumentParser(add_help=False, exit_on_error=False)
        if hasattr(self, "Arguments") and self.Arguments is not None:
            pydantic_parser = PydanticArgumentParser(self.Arguments)
            pydantic_parser.add_arguments_to_parser(parser)

        # Parse known args (ignore missing required ones) - suppress any errors
        old_stderr = sys.stderr
        sys.stderr = io.StringIO()

        try:
            parsed_args, _ = parser.parse_known_args(provided_args)
            args_dict = vars(parsed_args)
        except SystemExit:
            # parse_known_args can still raise SystemExit for required args
            # Just start with empty dict
            args_dict = {}
        except Exception:
            # If any other error, start with empty dict
            args_dict = {}
        finally:
            # Always restore stderr
            sys.stderr = old_stderr

        # Get all fields from the Pydantic model
        model_fields = self.Arguments.model_fields

        print("\n📝 Please provide the following required information:\n")

        # Prompt for missing required fields
        for field_name, field_info in model_fields.items():
            # Skip if already provided and has a value
            if field_name in args_dict and args_dict[field_name] is not None:
                # For booleans, False is a valid value
                if field_info.annotation is bool or args_dict[field_name] not in [
                    None,
                    "",
                ]:
                    continue

            # Check if field is required
            is_required = field_info.is_required()
            default = field_info.default
            description = field_info.description or field_name.replace("_", " ").title()
            field_type = field_info.annotation

            # Handle Optional types
            from typing import Union

            origin = get_origin(field_type)
            type_args = get_args(field_type)
            if origin is Union and type(None) in type_args:
                is_required = False

            # Skip optional fields with defaults
            if not is_required and default is not None and default is not ...:
                if field_name not in args_dict or args_dict[field_name] is None:
                    args_dict[field_name] = default
                continue

            # Prompt for the field
            prompt_text = f"{description}"
            if field_type is bool:
                prompt_text += " (yes/no)"
            if not is_required:
                prompt_text += " [optional]"
            prompt_text += ": "

            # Get user input
            while True:
                try:
                    user_input = input(prompt_text).strip()

                    # Allow skipping optional fields
                    if not is_required and not user_input:
                        args_dict[field_name] = None
                        break

                    # Require input for required fields
                    if is_required and not user_input:
                        print(f"  ❌ {description} is required. Please provide a value.")
                        continue

                    # Type conversion
                    if field_type is bool:
                        args_dict[field_name] = user_input.lower() in (
                            "yes",
                            "y",
                            "true",
                            "1",
                        )
                    elif field_type is int:
                        args_dict[field_name] = int(user_input)
                    elif field_type is float:
                        args_dict[field_name] = float(user_input)
                    else:
                        args_dict[field_name] = user_input

                    break
                except ValueError as e:
                    print(f"  ❌ Invalid input: {e}. Please try again.")
                except KeyboardInterrupt:
                    print("\n\n❌ Operation cancelled by user.")
                    sys.exit(1)

        # Validate with Pydantic
        try:
            print()  # Empty line for spacing
            return self.Arguments(**args_dict)
        except ValidationError as e:
            error_messages = []
            for error in e.errors():
                field = " -> ".join(str(loc) for loc in error["loc"])
                message = error["msg"]
                error_messages.append(f"  • {field}: {message}")

            print("❌ Validation failed:\n" + "\n".join(error_messages))
            raise CommandValidationError(f"Argument validation failed: {e}")

    def execute(self, args: ARG_TYPE) -> int:
        """
        Execute the command with the given arguments.

        Args:
            args: List of argument strings

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        self.handle(args)
        return 0

    @abstractmethod
    def handle(self, args: Any) -> None:
        """
        Command logic goes here.

        This method must be implemented by subclasses.

        Args:
            args: Parsed arguments (Pydantic model instance or argparse Namespace)
        """
        pass

    def print_message(self, message: str) -> None:
        """Print a message to stdout."""
        print(message)

    def print_error(self, message: str) -> None:
        """Print an error message to stderr."""
        print(message, file=sys.stderr)

    def print_success(self, message: str) -> None:
        """Print a success message (can be styled in subclasses)."""
        self.print_message(message)

    def print_warning(self, message: str) -> None:
        """Print a warning message (can be styled in subclasses)."""
        self.print_message(f"Warning: {message}")


class Command(BaseCommand):  # type: ignore[type-arg]
    """
    Convenience alias for BaseCommand.

    Both names can be used interchangeably.
    """

    pass


class CommandError(Exception):
    """Base exception for command errors."""

    pass
