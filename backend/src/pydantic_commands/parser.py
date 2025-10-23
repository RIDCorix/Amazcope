"""Pydantic to argparse converter."""

import argparse
from enum import Enum
from pathlib import Path
from typing import Any, Union, get_args, get_origin

from pydantic import BaseModel
from pydantic.fields import FieldInfo


class PydanticArgumentParser:
    """
    Converts Pydantic models to argparse arguments.

    This class analyzes a Pydantic model's fields and generates
    appropriate argparse arguments with type conversion and validation.
    """

    def __init__(self, model: type[BaseModel]) -> None:
        """
        Initialize the parser with a Pydantic model.

        Args:
            model: Pydantic model class to convert
        """
        self.model = model

    def add_arguments_to_parser(self, parser: argparse.ArgumentParser) -> None:
        """
        Add arguments from the Pydantic model to an ArgumentParser.

        Args:
            parser: ArgumentParser to add arguments to
        """
        for field_name, field_info in self.model.model_fields.items():
            self._add_field_argument(parser, field_name, field_info)

    def _add_field_argument(
        self, parser: argparse.ArgumentParser, field_name: str, field_info: FieldInfo
    ) -> None:
        """
        Add a single field as an argument.

        Args:
            parser: ArgumentParser to add argument to
            field_name: Name of the field
            field_info: Pydantic FieldInfo object
        """
        # Get field type and metadata
        field_type = field_info.annotation
        description = field_info.description or ""
        default = field_info.default
        is_required = field_info.is_required()

        # Parse type hints
        origin = get_origin(field_type)
        args = get_args(field_type)

        # Handle Optional types
        if origin is Union:
            # Check if it's Optional (Union[X, None])
            if type(None) in args:
                is_required = False
                # Get the non-None type
                field_type = next(arg for arg in args if arg is not type(None))
                origin = get_origin(field_type)
                args = get_args(field_type)

        # Determine argument name
        arg_name = field_name.replace("_", "-")

        # If not required or has a default, make it an optional flag with --
        if not is_required or (default is not None and default is not ...):
            arg_name = f"--{arg_name}"

        # Build argument kwargs
        kwargs: dict[str, Any] = {
            "help": description,
        }

        # Add default if present and not required
        if not is_required and default is not None and default is not ...:
            kwargs["default"] = default

        # Handle different types
        if origin is list or origin is list:
            # List type
            item_type = args[0] if args else str
            kwargs["nargs"] = "*" if not is_required else "+"
            kwargs["type"] = self._get_type_converter(item_type)
        elif self._is_bool_type(field_type):  # type: ignore[arg-type]
            # Boolean flag
            if is_required:
                # Required boolean should be a choice
                kwargs["type"] = self._str_to_bool
                kwargs["choices"] = [True, False]
            else:
                # Optional boolean is a store_true/store_false flag
                action = "store_true" if not default or default is ... else "store_false"
                kwargs["action"] = action
                if "type" in kwargs:
                    del kwargs["type"]
        elif self._is_enum_type(field_type):  # type: ignore[arg-type]
            # Enum type
            kwargs["type"] = str
            kwargs["choices"] = [e.value for e in field_type]  # type: ignore[union-attr]
        else:
            # Standard type
            kwargs["type"] = self._get_type_converter(field_type)  # type: ignore[arg-type]

        # Mark as required if needed (for optional flags)
        if is_required and arg_name.startswith("--"):
            kwargs["required"] = True

        parser.add_argument(arg_name, **kwargs)

    def _get_type_converter(self, field_type: type) -> Any:
        """
        Get the appropriate type converter for argparse.

        Args:
            field_type: Python type

        Returns:
            Converter function for argparse
        """
        # Handle basic types
        if field_type in (str, int, float):
            return field_type

        # Handle Path
        if field_type is Path:
            return Path

        # Handle bool
        if self._is_bool_type(field_type):
            return self._str_to_bool

        # Handle enum
        if self._is_enum_type(field_type):
            return str

        # Default to string
        return str

    @staticmethod
    def _is_bool_type(field_type: type) -> bool:
        """Check if a type is bool."""
        return field_type is bool

    @staticmethod
    def _is_enum_type(field_type: type) -> bool:
        """Check if a type is an Enum."""
        try:
            return isinstance(field_type, type) and issubclass(field_type, Enum)
        except TypeError:
            return False

    @staticmethod
    def _str_to_bool(value: str) -> bool:
        """Convert string to boolean."""
        if isinstance(value, bool):
            return value
        if value.lower() in ("yes", "true", "t", "y", "1"):
            return True
        if value.lower() in ("no", "false", "f", "n", "0"):
            return False
        raise argparse.ArgumentTypeError(f"Boolean value expected, got: {value}")
