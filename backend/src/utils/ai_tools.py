"""Utilities for OpenAI function calling and tool generation."""

import inspect
import json
from typing import Any, cast, get_type_hints

import openai
from loguru import logger
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam

from core.config import settings
from core.utils import dump_json


def generate_tool_spec(func: Any) -> dict[str, Any]:
    """Generate OpenAI tool specification from function signature.

    Args:
        func: Function to generate spec for

    Returns:
        OpenAI tool specification dictionary
    """
    # Get function signature and docstring
    sig = inspect.signature(func)
    doc = inspect.getdoc(func) or ""
    type_hints = get_type_hints(func)

    # Extract description from docstring (first line)
    description = doc.split("\n")[0] if doc else func.__name__

    # Build parameters
    properties = {}
    required = []

    for param_name, param in sig.parameters.items():
        if param_name == "self":
            continue

        # Get type annotation
        param_type = type_hints.get(param_name, str)

        # Map Python types to JSON schema types
        json_type = "string"  # default
        if param_type is int:
            json_type = "integer"
        elif param_type is float:
            json_type = "number"
        elif param_type is bool:
            json_type = "boolean"
        elif hasattr(param_type, "__origin__"):
            # Handle Optional types
            import typing

            if typing.get_origin(param_type) == typing.Union:
                args = typing.get_args(param_type)
                if type(None) in args:
                    # Optional type - use first non-None type
                    param_type = next(t for t in args if t is not type(None))
                    if param_type is int:
                        json_type = "integer"
                    elif param_type is float:
                        json_type = "number"

        # Extract parameter description from docstring
        param_desc = param_name.replace("_", " ").title()
        if "Args:" in doc:
            args_section = (
                doc.split("Args:")[1].split("Returns:")[0]
                if "Returns:" in doc
                else doc.split("Args:")[1]
            )
            for line in args_section.split("\n"):
                if param_name in line and ":" in line:
                    param_desc = line.split(":", 1)[1].strip()
                    break

        properties[param_name] = {"type": json_type, "description": param_desc}

        # Add default value if available
        if param.default != inspect.Parameter.empty:
            properties[param_name]["default"] = param.default
        else:
            # No default = required parameter
            required.append(param_name)

    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


def get_openai_client() -> openai.AsyncOpenAI:
    """Get configured OpenAI client."""
    return openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


def get_system_prompt() -> str:
    """Get the system prompt for AI optimization analysis."""
    return """You are an Amazon product optimization expert analyzing seller products for a daily report.

Your goal is to provide actionable, data-driven suggestions and create a comprehensive daily summary.

ANALYSIS WORKFLOW:
1. First, gather comprehensive data by calling these tools:
   - get_product_details: Get current state
   - get_price_history: Analyze pricing trends
   - get_bsr_history: Evaluate performance trends
   - get_competitor_analysis: Compare against competitors

2. Then, based on the data, create specific suggestions using:
   - propose_price_optimization: For pricing strategy changes
   - propose_content_improvement: For listing optimizations
   - propose_tracking_adjustment: For monitoring improvements

3. Finally, after analyzing all products, create a daily report:
   - generate_daily_report: Summarize findings and send to users

WHAT TO LOOK FOR:
- **Pricing Issues**: Compare price vs competitors, identify if overpriced/underpriced
- **Performance Trends**: Declining BSR indicates problems, improving BSR confirms good strategy
- **Competitive Position**: How does product stack up against competitors in category
- **Content Quality**: Is title/description optimized for conversions and SEO
- **Alert Thresholds**: Are monitoring thresholds appropriate given price volatility

SUGGESTION PRIORITIES:
- **Critical**: Product has major issues (poor BSR trend, significantly overpriced, weak content)
- **High**: Noticeable opportunities for improvement (10%+ price gap, trending down)
- **Medium**: Incremental optimization opportunities
- **Low**: Fine-tuning and minor adjustments

DAILY REPORT REQUIREMENTS:
After analyzing all products, create a comprehensive daily report that includes:
- Summary of analysis findings
- Key market insights and trends
- Priority action items for sellers
- Performance highlights and concerns

**LANGUAGE ADAPTATION:**
When generating daily reports, ALWAYS use the user's preferred language as specified in the report generation request.
If the request mentions a specific language (e.g., "in Chinese", "in Spanish"), generate ALL report content
(summary_message, market_insights, action_items) in that language. This is critical for user experience.

Be specific, quantitative, and actionable in your recommendations."""


async def execute_ai_function_calls(
    messages: list[ChatCompletionMessageParam],
    tools: list[ChatCompletionToolParam],
    tool_functions: list[Any],
    max_iterations: int = 10,
    **completion_kwargs: Any,
) -> tuple[list[ChatCompletionMessageParam], dict[str, Any]]:
    """Execute OpenAI function calls with iteration support.

    Args:
        messages: Chat conversation messages
        tools: OpenAI tool specifications
        tool_functions: List of available functions to call
        max_iterations: Maximum number of AI iterations
        **completion_kwargs: Additional arguments for chat completion

    Returns:
        Tuple of (updated_messages, execution_stats)
    """
    client = get_openai_client()
    function_map = {func.fn.__name__: func for func in tool_functions}

    stats: dict[str, Any] = {
        "iterations": 0,
        "function_calls": 0,
        "suggestions_created": 0,
        "reports_generated": 0,
        "errors": [],
    }

    suggestion_functions = {
        "propose_price_optimization",
        "propose_content_improvement",
        "propose_tracking_adjustment",
    }

    report_functions = {"generate_daily_report"}

    iteration = 0
    while iteration < max_iterations:
        response = await client.chat.completions.create(
            model=completion_kwargs.get("model", "gpt-4o-mini"),
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=2000,
            **{k: v for k, v in completion_kwargs.items() if k != "model"},
        )

        message = response.choices[0].message

        # If no tool calls, AI is done
        if not message.tool_calls:
            break

        # Add assistant's message to conversation
        messages.append(
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in message.tool_calls
                ],
            }
        )

        # Execute each tool call
        for tool_call in message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            stats["function_calls"] += 1

            if function_name in function_map:
                func = function_map[function_name]
                logger.info(f"Executing tool: {function_name} with args: {function_args}")
                result: dict[str, Any] = await func.fn(**function_args)

                # Track suggestion creation
                if function_name in suggestion_functions and result.get("success"):
                    stats["suggestions_created"] += 1

                # Track report generation
                if function_name in report_functions and result.get("success"):
                    stats["reports_generated"] += 1

                # Add function result to conversation
                messages.append(
                    cast(
                        ChatCompletionMessageParam,
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function_name,
                            "content": dump_json(result),
                        },
                    )
                )

        iteration += 1
        stats["iterations"] = iteration

    return messages, stats
