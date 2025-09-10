# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

## Project Overview

This is a **production-ready** YouTube Transcript MCP Server that fetches transcripts from YouTube videos using **yt-dlp CLI** for reliable subtitle extraction. It provides AI systems with the ability to extract, search, and analyze YouTube video transcripts through the Model Context Protocol (MCP).

**Status:** Fully functional with CLI-based implementation that bypasses YouTube's rate limiting.

## Quick Commands

### Running the Server

```bash
# Production (HTTP transport)
uvicorn src.server:app --host 0.0.0.0 --port 8080

# Development (STDIO transport)
python src/server.py

# Health check
curl http://localhost:8080/health
```

### Testing Tools

```bash
# Discover tools
mcp tools .venv/bin/python src/server.py

# Test transcript fetching
mcp call get_transcript --params '{"video_id":"jNQXAC9IVRw"}' .venv/bin/python src/server.py

# Test with time filtering
mcp call get_transcript --params '{"video_id":"jNQXAC9IVRw", "start_time": 10, "end_time": 60}' .venv/bin/python src/server.py

# Test search
mcp call search_transcript --params '{"video_id":"jNQXAC9IVRw", "query":"example"}' .venv/bin/python src/server.py

# Test summary analytics
mcp call get_transcript_summary --params '{"video_id":"jNQXAC9IVRw"}' .venv/bin/python src/server.py

# Test language detection
mcp call get_available_languages --params '{"video_id":"jNQXAC9IVRw"}' .venv/bin/python src/server.py
```

## Available Tools

1. **get_transcript** - Fetch video transcripts with optional time filtering
2. **search_transcript** - Search for specific text within transcripts with context
3. **get_transcript_summary** - Advanced analytics including pace, filler words, top words, content indicators
4. **get_available_languages** - List available transcript languages

## Key Features

- **Universal MCP Client Compatibility**: Time parameters accept integers, floats, strings, or nulls
- **CLI-Based Implementation**: Uses yt-dlp subprocess to avoid rate limiting
- **Multi-Language Support**: 100+ languages with auto-generated and manual transcripts
- **Advanced Analytics**: Speaking pace, filler words, content analysis, engagement metrics
- **Dual Transport**: Both STDIO and HTTP transport modes
- **Docker Support**: Multi-stage Alpine build with health checks

## Essential Dependencies

- `fastmcp>=0.9.0` - MCP server framework
- `yt-dlp>=2025.8.11` - YouTube transcript extraction via CLI
- `pydantic>=2.0.0` - Data validation and models
- `uvicorn>=0.24.0` - ASGI server for HTTP transport

## Environment Variables

```bash
YT_TRANSCRIPT_SERVER_PORT=8080    # Server port (default: 8080)
YT_TRANSCRIPT_SERVER_HOST=0.0.0.0 # Server host (default: 0.0.0.0)
YT_TRANSCRIPT_DEBUG=false         # Debug mode
```

## Package Management

This project uses `uv` for package management:

```bash
# Install dependencies
uv pip install -e .

# Add new dependency
uv add <package_name>
```

## Project Structure

```
src/
├── server.py          # Main MCP server
├── tools/             # MCP tool implementations
│   └── transcript_tools.py
├── models/            # Pydantic data models
│   └── transcript.py
tests/                 # Test files
└── README.md
```

## Transport Compatibility

**STDIO Transport** (Default): `python src/server.py`
**HTTP Transport** (Production): `uvicorn src.server:app --port 8080`

Server automatically selects transport based on startup method.

## Common Patterns for Claude Code

When working with this codebase:

1. **Tool Enhancement**: Add new transcript tools in `src/tools/transcript_tools.py`
2. **Model Updates**: Extend Pydantic models in `src/models/transcript.py`
3. **Error Handling**: Use `ToolError` for user-facing errors
4. **Video ID Handling**: Support both video IDs and full YouTube URLs
5. **Testing**: Use `mcp call` commands with various video types and edge cases

## Configuration Patterns

Always use absolute paths and proper error handling. For configuration that needs to be set before tool execution, use the pattern:

```python
@mcp.tool()
async def my_tool():
    from src.config.settings import CONFIG_VALUE  # Import inside function
    # Use CONFIG_VALUE here
```

## Troubleshooting

- **Tool not found**: Check `@mcp.tool()` decorator
- **Validation errors**: Video IDs must be 11 characters, times must be non-negative
- **Time filtering issues**: Parameters accept multiple formats (int, float, string, null)
- **Transport issues**: Use `uvicorn` for HTTP, `python src/server.py` for STDIO