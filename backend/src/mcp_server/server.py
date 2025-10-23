"""MCP Server for Amazcope Product Tracking System.

Provides tools and resources for AI agents to interact with product data,
metrics, alerts, and optimization features.
"""

from fastmcp import FastMCP

# Initialize FastMCP server
mcp_server = FastMCP(
    name="amazcope-mcp-server",
    version="1.0.0",
)


# Import tools and resources after server initialization
from . import resources, tools  # noqa: E402, F401

__all__ = ["mcp_server"]
