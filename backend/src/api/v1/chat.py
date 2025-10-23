"""Chat API endpoints with MCP integration.

Provides chat functionality with AI assistant that can access
product data and perform actions through MCP tools.
"""

# ChatCompletionMessageParam
from typing import Any, cast

from fastapi import APIRouter, Depends
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam
from pydantic import BaseModel

from api.deps import get_current_user
from core.config import settings
from mcp_server import tools  # noqa: F401 - Import to register tools
from users.models import User

router = APIRouter()


# Initialize OpenAI client
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


class ChatMessage(BaseModel):
    """Chat message model."""

    role: str
    content: str


class ChatRequest(BaseModel):
    """Chat request model."""

    messages: list[ChatMessage]
    context: dict[str, Any] | None = None


class ChatResponse(BaseModel):
    """Chat response model."""

    message: ChatMessage
    tool_calls: list[dict[str, Any]] | None = None


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    """Handle chat messages with AI assistant.

    The assistant can access product data and perform actions through MCP tools.
    """
    # Import MCP tools dynamically
    from mcp_server.tools import (
        get_bsr_history,
        get_competitor_analysis,
        get_price_history,
        get_product_details,
        get_user_products,
        search_products,
        trigger_product_refresh,
    )

    # Define available tools for OpenAI
    tools_definition: list[ChatCompletionToolParam] = [  # type: ignore[assignment]
        {
            "type": "function",
            "function": {
                "name": "get_product_details",
                "description": "Get detailed information about a specific product including current price, BSR, rating, and metadata",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_id": {
                            "type": "integer",
                            "description": "The ID of the product to retrieve",
                        }
                    },
                    "required": ["product_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "search_products",
                "description": "Search for products based on filters like title, ASIN, marketplace, or category",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search term to filter by title or ASIN",
                        },
                        "marketplace": {
                            "type": "string",
                            "description": "Filter by marketplace (US, UK, DE, etc.)",
                        },
                        "category": {
                            "type": "string",
                            "description": "Filter by product category",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results (default: 10)",
                            "default": 10,
                        },
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_price_history",
                "description": "Get price history for a product over a specified time period",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_id": {
                            "type": "integer",
                            "description": "The ID of the product",
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days of history to retrieve (default: 30)",
                            "default": 30,
                        },
                    },
                    "required": ["product_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_bsr_history",
                "description": "Get Best Seller Rank (BSR) history for a product",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_id": {
                            "type": "integer",
                            "description": "The ID of the product",
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days of history (default: 30)",
                            "default": 30,
                        },
                    },
                    "required": ["product_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_competitor_analysis",
                "description": "Get competitor analysis and comparison data for a product",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_id": {
                            "type": "integer",
                            "description": "The ID of the product",
                        }
                    },
                    "required": ["product_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "trigger_product_refresh",
                "description": "Trigger a manual refresh/scrape of product data from Amazon",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_id": {
                            "type": "integer",
                            "description": "The ID of the product to refresh",
                        }
                    },
                    "required": ["product_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_user_products",
                "description": "Get all products tracked by the current user",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of products (default: 20)",
                            "default": 20,
                        }
                    },
                },
            },
        },
    ]

    # Build system message with context
    system_message = f"""You are an AI assistant for Amazcope, an Amazon product tracking and optimization system.

You help users understand their product data, analyze trends, and get insights about their Amazon listings.

Current user: {current_user.username} (ID: {current_user.id})

You have access to the following tools:
- get_product_details: Get detailed info about a specific product
- search_products: Search for products by title, ASIN, marketplace, or category
- get_price_history: Get historical price data
- get_bsr_history: Get Best Seller Rank history
- get_competitor_analysis: Compare product with competitors
- trigger_product_refresh: Manually update product data
- get_user_products: List all products tracked by user

When users ask about products, use the tools to fetch real data. Be helpful, concise, and data-driven."""

    # Add context if provided
    if request.context:
        context_info = []
        if "product_id" in request.context:
            context_info.append(f"Current product ID: {request.context['product_id']}")
        if "page" in request.context:
            context_info.append(f"Current page: {request.context['page']}")

        if context_info:
            system_message += "\n\nContext:\n" + "\n".join(context_info)

    # Prepare messages
    messages: list[ChatCompletionMessageParam] = [
        cast(ChatCompletionMessageParam, {"role": "system", "content": system_message})
    ]
    for msg in request.messages:
        messages.append(
            cast(ChatCompletionMessageParam, {"role": msg.role, "content": msg.content})
        )

    # Call OpenAI API
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=tools_definition,
        tool_choice="auto",
    )

    assistant_message = response.choices[0].message

    # Handle tool calls if present
    tool_call_results = []
    if assistant_message.tool_calls:
        for tool_call in assistant_message.tool_calls:
            function_name = tool_call.function.name
            function_args = eval(tool_call.function.arguments)

            # Execute the tool
            tool_result = None
            if function_name == "get_product_details":
                tool_result = await get_product_details.fn(**function_args)
            elif function_name == "search_products":
                tool_result = await search_products.fn(**function_args)
            elif function_name == "get_price_history":
                tool_result = await get_price_history.fn(**function_args)
            elif function_name == "get_bsr_history":
                tool_result = await get_bsr_history.fn(**function_args)
            elif function_name == "get_competitor_analysis":
                tool_result = await get_competitor_analysis.fn(**function_args)
            elif function_name == "trigger_product_refresh":
                tool_result = await trigger_product_refresh.fn(**function_args)
            elif function_name == "get_user_products":
                # Add user_id to args
                function_args["user_id"] = current_user.id
                tool_result = await get_user_products.fn(**function_args)

            tool_call_results.append(
                {
                    "tool_call_id": tool_call.id or "",
                    "function_name": function_name,
                    "result": tool_result,
                }
            )

        # If there were tool calls, make another API call with results
        if tool_call_results:
            messages.append(
                dict(
                    role="assistant",
                    content=assistant_message.content,
                    tool_calls=[
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in assistant_message.tool_calls
                    ],
                )
            )

            for tool_result in tool_call_results:
                messages.append(
                    cast(
                        ChatCompletionMessageParam,
                        dict(
                            role="tool",
                            tool_call_id=tool_result["tool_call_id"] or "",
                            content=str(tool_result["result"]),
                        ),
                    )
                )

            # Make final call with tool results
            final_response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
            )

            final_message = final_response.choices[0].message
            return ChatResponse(
                message=ChatMessage(
                    role="assistant",
                    content=final_message.content or "",
                ),
                tool_calls=[
                    {
                        "function": tr["function_name"],
                        "result": tr["result"],
                    }
                    for tr in tool_call_results
                ],
            )

    return ChatResponse(
        message=ChatMessage(
            role="assistant",
            content=assistant_message.content or "",
        ),
        tool_calls=None,
    )


@router.get("/chat/context")
async def get_chat_context(
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Get context information for chat initialization."""

    return {
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
        },
    }
