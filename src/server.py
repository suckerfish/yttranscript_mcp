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


# Create the MCP server instance
mcp = FastMCP(
    name="YouTube Transcript Server",
    version="0.1.0",
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


@mcp.prompt()
def summarize_video(video_id: str, language_code: str = "en") -> str:
    """Generate a prompt to summarize a YouTube video transcript."""
    return (
        f"Please fetch the transcript for YouTube video '{video_id}' "
        f"(language: {language_code}) using the get_transcript tool, "
        f"then provide a comprehensive summary including:\n"
        f"- Main topics and key points\n"
        f"- Important quotes or statements\n"
        f"- Overall tone and style of the content\n"
        f"- A brief one-paragraph summary"
    )


@mcp.prompt()
def search_topic_in_video(video_id: str, topic: str) -> str:
    """Generate a prompt to search for a specific topic within a YouTube video."""
    return (
        f"Please search the transcript of YouTube video '{video_id}' "
        f"for references to '{topic}' using the search_transcript tool, "
        f"then analyze the results:\n"
        f"- List all relevant mentions with timestamps\n"
        f"- Summarize what is said about '{topic}'\n"
        f"- Note the context around each mention\n"
        f"- Provide an overall assessment of how '{topic}' is covered"
    )


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
        default=8080,
        help='Port to run the server on (default: 8080)'
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
    
    if transport == "http" or args.port != 8080:
        # Use streamable HTTP with stateless mode for remote access
        mcp.run(
            transport="streamable-http",
            host=args.host,
            port=args.port,
            stateless_http=True
        )
    else:
        # Default STDIO for local testing
        mcp.run()


# For uvicorn compatibility (streamable HTTP with stateless mode)
app = mcp.http_app(stateless_http=True)


if __name__ == "__main__":
    main()