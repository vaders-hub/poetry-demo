"""
Simple MCP (Model Context Protocol) Server
Provides tools for database operations and text processing
"""

import asyncio
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from app.config import setting
from app.db import DatabaseSessionManager
from app.crud.customer import get_customers, get_customer


# Initialize MCP server
app = Server("poetry-demo-mcp-server")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="get_all_customers",
            description="Get all customers from the database",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_customer_by_id",
            description="Get a specific customer by their ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "The unique identifier of the customer"
                    }
                },
                "required": ["customer_id"]
            }
        ),
        Tool(
            name="calculate",
            description="Perform basic arithmetic calculations (add, subtract, multiply, divide)",
            inputSchema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["add", "subtract", "multiply", "divide"],
                        "description": "The arithmetic operation to perform"
                    },
                    "a": {
                        "type": "number",
                        "description": "First number"
                    },
                    "b": {
                        "type": "number",
                        "description": "Second number"
                    }
                },
                "required": ["operation", "a", "b"]
            }
        ),
        Tool(
            name="text_stats",
            description="Get statistics about a text string (length, word count, character count)",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to analyze"
                    }
                },
                "required": ["text"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""

    if name == "get_all_customers":
        return await handle_get_all_customers()

    elif name == "get_customer_by_id":
        customer_id = arguments.get("customer_id")
        return await handle_get_customer_by_id(customer_id)

    elif name == "calculate":
        operation = arguments.get("operation")
        a = arguments.get("a")
        b = arguments.get("b")
        return handle_calculate(operation, a, b)

    elif name == "text_stats":
        text = arguments.get("text")
        return handle_text_stats(text)

    else:
        return [TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]


async def handle_get_all_customers() -> list[TextContent]:
    """Get all customers from database."""
    try:
        db_manager = DatabaseSessionManager()
        db_manager.init(setting.database_url)

        async with db_manager.session() as session:
            customers = await get_customers(session)

            result = "Customers:\n"
            for customer in customers:
                result += f"- ID: {customer.customer_id}, Name: {customer.name}, "
                result += f"Address: {customer.address or 'N/A'}, "
                result += f"Website: {customer.website or 'N/A'}, "
                result += f"Credit Limit: {customer.credit_limit or 0}\n"

            return [TextContent(type="text", text=result)]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error retrieving customers: {str(e)}"
        )]


async def handle_get_customer_by_id(customer_id: str) -> list[TextContent]:
    """Get a specific customer by ID."""
    try:
        db_manager = DatabaseSessionManager()
        db_manager.init(setting.database_url)

        async with db_manager.session() as session:
            customer = await get_customer(session, customer_id)

            result = f"Customer Details:\n"
            result += f"ID: {customer.customer_id}\n"
            result += f"Name: {customer.name}\n"
            result += f"Address: {customer.address or 'N/A'}\n"
            result += f"Website: {customer.website or 'N/A'}\n"
            result += f"Credit Limit: {customer.credit_limit or 0}\n"

            return [TextContent(type="text", text=result)]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error retrieving customer {customer_id}: {str(e)}"
        )]


def handle_calculate(operation: str, a: float, b: float) -> list[TextContent]:
    """Perform arithmetic calculation."""
    try:
        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        elif operation == "divide":
            if b == 0:
                return [TextContent(
                    type="text",
                    text="Error: Division by zero"
                )]
            result = a / b
        else:
            return [TextContent(
                type="text",
                text=f"Unknown operation: {operation}"
            )]

        return [TextContent(
            type="text",
            text=f"{a} {operation} {b} = {result}"
        )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error performing calculation: {str(e)}"
        )]


def handle_text_stats(text: str) -> list[TextContent]:
    """Get text statistics."""
    try:
        char_count = len(text)
        word_count = len(text.split())
        line_count = len(text.splitlines())

        # Character frequency
        char_freq = {}
        for char in text.lower():
            if char.isalnum():
                char_freq[char] = char_freq.get(char, 0) + 1

        # Most common characters
        top_chars = sorted(char_freq.items(), key=lambda x: x[1], reverse=True)[:5]

        result = f"Text Statistics:\n"
        result += f"Characters: {char_count}\n"
        result += f"Words: {word_count}\n"
        result += f"Lines: {line_count}\n"
        result += f"\nMost common characters:\n"
        for char, count in top_chars:
            result += f"  '{char}': {count}\n"

        return [TextContent(type="text", text=result)]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error analyzing text: {str(e)}"
        )]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
