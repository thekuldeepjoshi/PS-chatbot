"""Small stdio client for testing the MCP server locally."""

import asyncio
import json
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    server = StdioServerParameters(
        command="python",
        args=[str(Path(__file__).with_name("server.py"))],
    )

    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Available tools:")
            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")

            result = await session.call_tool("get_total_revenue", {})
            print("\nTotal revenue:")
            for item in result.content:
                if hasattr(item, "text"):
                    print(item.text)

            result = await session.call_tool("get_top_customers", {"limit": 2})
            print("\nTop customers:")
            for item in result.content:
                if hasattr(item, "text"):
                    try:
                        print(json.dumps(json.loads(item.text), indent=2))
                    except json.JSONDecodeError:
                        print(item.text)


if __name__ == "__main__":
    asyncio.run(main())
