#!/bin/bash
# Dramatiq worker entrypoint script

uv run dramatiq core.dramatiq_app products.tasks --processes 2 --threads 4
