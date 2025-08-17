"""Tool implementations for YouTube transcript MCP server."""

# Handle both direct execution and module imports
try:
    from .transcript_tools import register_transcript_tools
except ImportError:
    from transcript_tools import register_transcript_tools

__all__ = ["register_transcript_tools"]