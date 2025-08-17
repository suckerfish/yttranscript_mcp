"""YouTube Transcript MCP Server

A FastMCP server that provides YouTube transcript fetching capabilities
using streamable HTTP transport.
"""

import argparse
import os
import sys
from pathlib import Path

# Add the src directory to the path for direct execution
if __name__ == "__main__":
    src_path = Path(__file__).parent
    sys.path.insert(0, str(src_path))

from fastmcp import FastMCP

# Handle both direct execution and module imports
try:
    from .tools.transcript_tools import register_transcript_tools
except ImportError:
    from tools.transcript_tools import register_transcript_tools


# Create the MCP server instance with stateless HTTP for reliable deployment
mcp = FastMCP(
    name="YouTube Transcript Server",
    version="0.1.0",
    stateless_http=True  # Required for reliable remote deployment
)

# Register all transcript tools
register_transcript_tools(mcp)


@mcp.resource("app://info")
def get_server_info() -> dict:
    """Get information about the YouTube Transcript MCP server."""
    return {
        "name": "YouTube Transcript Server",
        "version": "0.1.0",
        "description": "MCP server for fetching YouTube video transcripts",
        "supported_features": [
            "transcript_fetching",
            "multi_language_support", 
            "transcript_search",
            "language_detection",
            "summary_generation"
        ],
        "transport": "streamable_http",
        "api_version": "2024-11-05"
    }


# Add health check endpoint for production deployment
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    """Health check endpoint for production monitoring."""
    from starlette.responses import JSONResponse
    return JSONResponse({
        "status": "healthy",
        "version": "0.1.0",
        "service": "YouTube Transcript MCP Server"
    })


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='YouTube Transcript MCP Server')
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='Port to run the server on (default: 8000)'
    )
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Host to bind the server to (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    return parser.parse_args()


def main():
    """Main entry point for the MCP server."""
    args = parse_arguments()
    
    # Set environment variables from arguments
    os.environ['YT_TRANSCRIPT_SERVER_PORT'] = str(args.port)
    os.environ['YT_TRANSCRIPT_SERVER_HOST'] = args.host
    if args.debug:
        os.environ['YT_TRANSCRIPT_DEBUG'] = 'true'
    
    # Determine transport mode
    transport = os.getenv("TRANSPORT", "stdio")
    
    if transport == "http" or args.port != 8000:
        # Use streamable HTTP with stateless mode for remote access
        mcp.run(
            transport="streamable-http",
            host=args.host,
            port=args.port
        )
    else:
        # Default STDIO for local testing
        mcp.run()


# For uvicorn compatibility (streamable HTTP)
app = mcp.http_app()


if __name__ == "__main__":
    main()