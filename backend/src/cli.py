#!/usr/bin/env python
"""Command-line interface for the application."""

from dotenv import load_dotenv

from core.database import discover_models
from pydantic_commands import host_cli

if __name__ == "__main__":
    load_dotenv()
    discover_models()
    host_cli()
