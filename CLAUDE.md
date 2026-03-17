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

### Docker / GHCR

```bash
# Pull and run from GHCR
docker run -d -p 8080:8080 ghcr.io/suckerfish/yttranscript_mcp:latest

# Or use compose
docker compose up -d
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

All tools are tagged `read` with `ToolAnnotations(readOnlyHint=True)`.

1. **get_transcript** - Fetch video transcripts with optional time filtering (with progress reporting)
2. **search_transcript** - Search for specific text within transcripts with context
3. **get_transcript_summary** - Advanced analytics including pace, filler words, top words, content indicators (with progress reporting)
4. **get_available_languages** - List available transcript languages

## Prompt Templates

- **summarize_video(video_id, language_code)** - Instructs the LLM to fetch and summarize a video transcript
- **search_topic_in_video(video_id, topic)** - Instructs the LLM to search for and analyze a topic within a video

## Key Features

- **Universal MCP Client Compatibility**: Time parameters accept integers, floats, strings, or nulls
- **CLI-Based Implementation**: Uses yt-dlp subprocess to avoid rate limiting
- **Multi-Language Support**: 100+ languages with auto-generated and manual transcripts
- **Advanced Analytics**: Speaking pace, filler words, content analysis, engagement metrics
- **Dual Transport**: Both STDIO and HTTP transport modes (stateless HTTP for production)
- **GHCR CI/CD**: GitHub Actions builds multi-arch (amd64/arm64) images on every push to main
- **Context Logging**: Tools use FastMCP Context for `ctx.info()`/`ctx.warning()` with progress reporting
- **Transcript Caching**: Module-level cache with 10-min TTL and 50-entry eviction
- **Retry Logic**: Automatic retries with backoff for yt-dlp timeouts and transient errors
- **MetaMCP Compatible**: NullContext shim ensures tools work when Context is not injected

## Essential Dependencies

- `fastmcp>=2.14.5,<3.0.0` - MCP server framework
- `yt-dlp` - YouTube transcript extraction via CLI
- `pydantic>=2.0.0` - Data validation and models (using v2 `field_validator`/`model_validator`)
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
├── server.py          # Main MCP server, prompts, health check
├── tools/             # MCP tool implementations
│   └── transcript_tools.py
├── models/            # Pydantic data models
│   └── transcript.py
.github/
└── workflows/
    └── docker.yml     # GHCR CI/CD (multi-arch build)
compose.yaml           # Docker Compose (pulls from GHCR)
Dockerfile             # Multi-stage build
tests/                 # Test files
```

## Transport Compatibility

**STDIO Transport** (Default): `python src/server.py`
**HTTP Transport** (Production): `uvicorn src.server:app --port 8080`

Both paths use `stateless_http=True` for compatibility with MCP clients that don't maintain sessions (e.g., MetaMCP).

## Deployment

The Komodo stack `yttranscript-mcp-gamma` pulls from `ghcr.io/suckerfish/yttranscript_mcp:latest`. On push to main:

1. GitHub Actions builds and pushes a multi-arch image to GHCR
2. Deploy via Komodo: `komodo_ops.py deploy-stack yttranscript-mcp-gamma`

## Common Patterns for Claude Code

When working with this codebase:

1. **Tool Enhancement**: Add new transcript tools in `src/tools/transcript_tools.py`
2. **Model Updates**: Extend Pydantic models in `src/models/transcript.py` (use `field_validator`/`model_validator`, not deprecated `validator`)
3. **Error Handling**: Use `ToolError` for user-facing errors
4. **Video ID Handling**: Support both video IDs and full YouTube URLs
5. **Context Usage**: All tools accept `ctx: Context = None` with `ctx = ctx or _null_ctx` for MetaMCP compatibility
6. **Tool Registration**: Use `tags={"read"}` and `annotations=ToolAnnotations(readOnlyHint=True)` on all read-only tools
7. **Testing**: Use `mcp call` commands with various video types and edge cases

## Troubleshooting

- **Tool not found**: Check `@mcp.tool()` decorator
- **Validation errors**: Video IDs must be 11 characters, times must be non-negative
- **Time filtering issues**: Parameters accept multiple formats (int, float, string, null)
- **Transport issues**: Use `uvicorn` for HTTP, `python src/server.py` for STDIO
- **Missing session ID**: Ensure `stateless_http=True` is set in both `mcp.run()` and `mcp.http_app()`
- **MetaMCP ctx errors**: Tools must use `ctx = ctx or _null_ctx` pattern since MetaMCP doesn't inject Context
