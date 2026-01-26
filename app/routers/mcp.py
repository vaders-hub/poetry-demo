"""
MCP (Model Context Protocol) Router
Provides endpoints to interact with the MCP server
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.utils import error_response, success_response

router = APIRouter(prefix="/mcp", tags=["mcp"])


class ToolCallRequest(BaseModel):
    """Request model for MCP tool calls."""

    tool_name: str
    arguments: dict[str, Any] | None = {}


class CalculateRequest(BaseModel):
    """Request model for calculate tool."""

    operation: str
    a: float
    b: float


class TextStatsRequest(BaseModel):
    """Request model for text stats tool."""

    text: str


class CustomerIdRequest(BaseModel):
    """Request model for getting customer by ID."""

    customer_id: str


@router.get("/tools")
async def list_available_tools():
    """
    List all available MCP tools.

    Returns information about tools that can be called via MCP server.
    """
    tools = [
        {
            "name": "get_all_customers",
            "description": "Get all customers from the database",
            "parameters": {},
        },
        {
            "name": "get_customer_by_id",
            "description": "Get a specific customer by their ID",
            "parameters": {"customer_id": "string (required)"},
        },
        {
            "name": "calculate",
            "description": "Perform basic arithmetic calculations",
            "parameters": {
                "operation": "string (add|subtract|multiply|divide)",
                "a": "number",
                "b": "number",
            },
        },
        {
            "name": "text_stats",
            "description": "Get statistics about a text string",
            "parameters": {"text": "string"},
        },
    ]

    return success_response(
        data=tools,
        message="사용 가능한 MCP 도구 목록",
        metadata={"tools_count": len(tools)},
    )


@router.post("/calculate")
async def calculate(request: CalculateRequest):
    """
    Perform arithmetic calculation using MCP calculator tool.

    Example:
    ```json
    {
        "operation": "add",
        "a": 10,
        "b": 20
    }
    ```
    """
    try:
        operations_map = {
            "add": lambda a, b: a + b,
            "subtract": lambda a, b: a - b,
            "multiply": lambda a, b: a * b,
            "divide": lambda a, b: a / b if b != 0 else None,
        }

        if request.operation not in operations_map:
            return error_response(
                message=f"잘못된 연산입니다. 사용 가능한 연산: {', '.join(operations_map.keys())}",
                error="INVALID_OPERATION",
                status_code=400,
            )

        if request.operation == "divide" and request.b == 0:
            return error_response(
                message="0으로 나눌 수 없습니다.",
                error="DIVISION_BY_ZERO",
                status_code=400,
            )

        result = operations_map[request.operation](request.a, request.b)

        return success_response(
            data={
                "operation": request.operation,
                "operands": {"a": request.a, "b": request.b},
                "result": result,
            },
            message=f"{request.operation} 연산이 완료되었습니다.",
        )

    except HTTPException:
        raise
    except Exception as e:
        return error_response(
            message="계산 중 오류가 발생했습니다.",
            error=str(e),
            status_code=500,
        )


@router.post("/text-stats")
async def text_statistics(request: TextStatsRequest):
    """
    Get statistics about a text string using MCP text_stats tool.

    Returns character count, word count, line count, and most common characters.

    Example:
    ```json
    {
        "text": "Hello World! This is a test."
    }
    ```
    """
    try:
        text = request.text

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
        top_chars_dict = dict(top_chars)

        return success_response(
            data={
                "character_count": char_count,
                "word_count": word_count,
                "line_count": line_count,
                "most_common_characters": top_chars_dict,
            },
            message="텍스트 통계가 계산되었습니다.",
        )

    except Exception as e:
        return error_response(
            message="텍스트 통계 계산 중 오류가 발생했습니다.",
            error=str(e),
            status_code=500,
        )


@router.get("/info")
async def mcp_info():
    """
    Get information about the MCP integration.

    Returns details about the MCP server and available tools.
    """
    return success_response(
        data={
            "mcp_server": {
                "name": "poetry-demo-mcp-server",
                "version": "1.0.0",
                "protocol": "Model Context Protocol (MCP)",
                "description": "Simple MCP server providing database operations and utility tools",
            },
            "integration": {
                "type": "FastAPI + MCP",
                "endpoints": [
                    "GET /mcp/tools - List available tools",
                    "GET /mcp/info - Get MCP server info",
                    "POST /mcp/calculate - Perform calculations",
                    "POST /mcp/text-stats - Get text statistics",
                ],
            },
            "tools_count": 4,
            "status": "active",
        },
        message="MCP 서버 정보",
    )


@router.get("/health")
async def mcp_health_check():
    """
    Check if MCP server is healthy and responding.
    """
    return success_response(
        data={"status": "healthy"}, message="MCP 서버가 정상 작동 중입니다."
    )
