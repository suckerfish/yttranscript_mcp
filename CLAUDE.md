# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **fully functional, production-ready** YouTube Transcript MCP Server that fetches transcripts from YouTube videos using **yt-dlp** for reliable subtitle extraction. It provides AI systems with the ability to extract, search, and analyze YouTube video transcripts through the Model Context Protocol (MCP).

**✅ Status:** **CLI MIGRATION COMPLETE** - MCP server fully migrated from hybrid yt-dlp + requests approach to pure CLI implementation (September 2025). This eliminates HTTP 429 rate limiting issues and provides reliable YouTube transcript extraction.

The server now uses **pure yt-dlp CLI** via subprocess execution instead of the problematic hybrid approach, providing consistent subtitle extraction that bypasses YouTube's anti-bot measures. Supports streamable HTTP transport with `stateless_http=True` for reliable deployment and provides comprehensive transcript functionality including multi-language support (100+ languages), search capabilities, and transcript summaries.

## Quick Commands

### Running the Server

For streamable HTTP (recommended):
```bash
# Production with uvicorn
uvicorn src.server:app --host 0.0.0.0 --port 8080

# Development with auto-reload
uvicorn src.server:app --host 0.0.0.0 --port 8080 --reload

# Direct Python execution (stdio mode)
python src/server.py --port 8000 --debug
```

### ✅ Current Testing Status (September 2025 - CLI Migration Complete)

**MCPTools CLI Testing - Pure CLI Implementation:**

```bash
# Health check (production deployment)
curl http://localhost:8080/health
# Returns: {"status":"healthy","version":"0.1.0","service":"YouTube Transcript MCP Server"}

# ✅ CLI MIGRATION VALIDATED:
# Tool discovery using MCPTools CLI
mcp tools .venv/bin/python src/server.py
# Returns: All 4 tools properly registered and discoverable

# ✅ TRANSCRIPT EXTRACTION WORKING:
# Basic transcript fetching (bypasses HTTP 429 issues)
mcp call get_transcript --params '{"video_id":"jNQXAC9IVRw"}' .venv/bin/python src/server.py
# Uses pure CLI implementation via subprocess

# Transcript fetching with timestamp filtering
mcp call get_transcript --params '{"video_id":"jNQXAC9IVRw", "start_time": 0, "end_time": 10}' .venv/bin/python src/server.py

# Language detection (uses yt-dlp library for metadata only)
mcp call get_available_languages --params '{"video_id":"9bZkp7q19f0"}' .venv/bin/python src/server.py

# Search functionality (uses CLI backend)
mcp call search_transcript --params '{"video_id":"jNQXAC9IVRw", "query":"elephant"}' .venv/bin/python src/server.py

# Summary generation (uses CLI backend)
mcp call get_transcript_summary --params '{"video_id":"jNQXAC9IVRw"}' .venv/bin/python src/server.py

# 🎯 CLI IMPLEMENTATION ADVANTAGES:
# - No more HTTP 429 rate limiting from direct requests
# - Consistent transcript extraction via yt-dlp CLI
# - Bypasses YouTube's anti-bot detection measures
```

### 🔧 Production Deployment Testing

```bash
# Test uvicorn streamable HTTP
uvicorn src.server:app --host 0.0.0.0 --port 8080

# Verify health endpoint
curl http://localhost:8080/health
# Expected: {"status":"healthy","version":"0.1.0","service":"YouTube Transcript MCP Server"}

# Test with different video formats
# ✅ Video IDs: KeRsFAiJGww  
# ✅ Full URLs: https://www.youtube.com/watch?v=KeRsFAiJGww
# ✅ Short URLs: https://youtu.be/KeRsFAiJGww
```

### 🐳 Docker Deployment (NEW - August 2025)

**Quick Start with Docker:**
```bash
# Build the Docker image
docker build -t yttranscript-mcp:latest .

# Run with docker-compose (recommended)
docker-compose up -d yttranscript-mcp

# Or run directly
docker run -d --name yttranscript-mcp -p 8080:8080 yttranscript-mcp:latest

# Test health endpoint
curl http://localhost:8080/health

# Test MCP tools in container
mcp tools docker run --rm -i yttranscript-mcp:latest python src/server.py

# Test specific tool
mcp call get_available_languages --params '{"video_id":"9bZkp7q19f0"}' docker run --rm -i yttranscript-mcp:latest python src/server.py
```

**Docker Features:**
- ✅ **Multi-stage Alpine build** for optimal size (~200MB final image)
- ✅ **Non-root user** for security
- ✅ **FFmpeg included** for yt-dlp compatibility  
- ✅ **Health checks** built-in
- ✅ **Both STDIO and HTTP transport** support
- ✅ **Resource limits** configured in docker-compose
- ✅ **Development mode** with auto-reload and volume mounts

**Docker Compose Profiles:**
```bash
# Production mode (default)
docker-compose up yttranscript-mcp

# Development mode with auto-reload
docker-compose --profile dev up yttranscript-mcp-dev
```

### Package Management

```bash
# Install dependencies manually
uv pip install -e .

# Add a new dependency
uv add <package_name>
```

**Note**: When using UV with MCP servers, add `[tool.hatch.build.targets.wheel]` and `packages = ["src"]` to pyproject.toml.

## Essential FastMCP Patterns

### Basic Server Setup
```python
from fastmcp import FastMCP

mcp = FastMCP("My MCP Server")

@mcp.tool()
async def example_tool(parameter: str) -> dict:
    """Tool documentation here."""
    return {"result": "value"}

if __name__ == "__main__":
    mcp.run()
```

### Input Validation with Pydantic
```python
from pydantic import BaseModel, Field

class UserRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., regex=r'^[\w\.-]+@[\w\.-]+\.\w+$')

@mcp.tool()
def create_user(request: UserRequest) -> dict:
    """Create user with validated input."""
    return {"user_id": "123", "name": request.name}
```

### Error Handling
```python
from fastmcp.exceptions import ToolError

@mcp.tool()
def safe_tool(param: str) -> str:
    try:
        # Your tool logic
        return result
    except ValueError as e:
        # Client sees generic error
        raise ValueError("Invalid input")
    except SomeError as e:
        # Client sees specific error
        raise ToolError(f"Tool failed: {str(e)}")
```

### Authentication Context
```python
from fastmcp import Context

@mcp.tool()
async def authenticated_tool(param: str, ctx: Context) -> dict:
    """Tool requiring authentication."""
    user_id = ctx.client_id
    scopes = ctx.scopes
    
    if "required_scope" not in scopes:
        raise ToolError("Insufficient permissions")
    
    return {"result": f"Hello user {user_id}"}
```

## Key Development Workflow

1. **Create Tools**: Define functions with `@mcp.tool()` decorator
2. **Test Locally**: Use `mcp tools python src/server.py` to verify tools work
3. **Add Validation**: Use Pydantic models for input validation
4. **Handle Errors**: Use `ToolError` for client-visible errors
5. **Test Integration**: Use `mcp shell python src/server.py` for interactive testing
6. **Deploy**: Configure for production deployment

## MCP Server Types

- **Local Servers**: Run as subprocesses, communicate via STDIO, good for file system access
- **Remote Servers**: Run as web services, support OAuth 2.1, better for SaaS integrations

## Transport Protocols

- **STDIO**: For local servers (subprocess communication)
- **Streamable HTTP**: Modern protocol for remote servers (recommended)
- **HTTP+SSE**: Legacy protocol for backward compatibility

## Project Structure

```
src/
├── server.py          # Main MCP server implementation
├── tools/             # Tool definitions organized by domain
├── resources/         # Resource handlers for static/dynamic data
├── models/            # Pydantic models for validation
└── config/            # Configuration and settings
```

## Essential Dependencies

- `fastmcp>=0.9.0` - MCP server framework
- `yt-dlp>=2025.8.11` - **Core CLI tool for fetching YouTube transcripts** (REPLACED youtube-transcript-api and requests)
- `pydantic>=2.0.0` - Data validation and models for transcript data structures
- `uvicorn>=0.24.0` - ASGI server for streamable HTTP transport

**Note:** `requests` dependency removed in CLI migration - all HTTP requests now handled by yt-dlp CLI subprocess execution.

## Comprehensive Documentation

For detailed implementation guidance, see:

- **[Quick Start Guide](docs/quickstart.md)** - Setup, basic server creation, first tools
- **[Authentication Guide](docs/authentication.md)** - OAuth 2.1, security patterns, context injection
- **[Deployment Guide](docs/deployment.md)** - Production deployment, Docker, cloud platforms
- **[Testing Guide](docs/testing.md)** - MCPTools usage, unit testing, integration testing
- **[Best Practices](docs/best-practices.md)** - Error handling, performance, security, code quality
- **[MCPTools Documentation](docs/mcptools.md)** - Detailed testing and validation guide

## Transport Compatibility

**✅ This MCP server supports BOTH transport methods:**

### 🔄 STDIO Transport (Default)
- **Usage**: `python src/server.py` (direct execution)
- **Best for**: Local development, testing, simple MCP client integrations
- **How it works**: Server communicates via standard input/output streams
- **MCP Client Config**: Point to `python src/server.py` command

### 🌐 Streamable HTTP Transport (Recommended for Production)  
- **Usage**: `uvicorn src.server:app --host 0.0.0.0 --port 8080`
- **Best for**: Remote deployments, cloud hosting, production environments
- **How it works**: HTTP server with `/mcp` endpoint for JSON-RPC communication
- **MCP Client Config**: Point to HTTP endpoint `http://host:port/mcp`
- **Features**: Health checks, better error handling, scalability

### 🔧 Automatic Transport Selection
The server automatically chooses transport based on how it's started:
```bash
# STDIO mode (default)
python src/server.py

# HTTP mode (when port specified or TRANSPORT=http)
python src/server.py --port 8000
TRANSPORT=http python src/server.py
uvicorn src.server:app --port 8080
```

## Available Tools (Pure CLI Implementation)

This server provides the following transcript tools with **pure yt-dlp CLI** backend:

1. **get_transcript**: ⭐ Primary tool - Fetch complete transcript using yt-dlp CLI subprocess with timestamp filtering support
2. **get_available_languages**: ⭐ Highly reliable - List all available transcript languages using yt-dlp library (metadata only)
3. **search_transcript**: ✅ Fully functional - Search for specific text within transcripts with context (CLI backend)
4. **get_transcript_summary**: ✅ Fully functional - Get summary statistics and sample text from transcripts (CLI backend)

**CLI Migration Complete** - All transcript fetching now uses subprocess execution to avoid HTTP 429 rate limiting issues.

## Auto-Generated Subtitle Support

The server is optimized for auto-generated subtitles (the most common transcript type on YouTube):

**Priority Logic:**
1. **Manual transcripts** (human-created) - highest quality
2. **Auto-generated transcripts** - most common, good quality
3. **Any available transcript** - fallback for edge cases

**Key Features:**
- Automatically detects transcript type (`is_generated: true/false`)
- Prioritizes auto-generated when manual transcripts aren't available
- Supports all languages with auto-generated subtitles
- Handles both video IDs and full YouTube URLs

## Common Patterns for Claude Code

When working with this codebase, focus on:

1. **Tool Enhancement**: Add new transcript tools in `src/tools/transcript_tools.py`
2. **Model Updates**: Extend Pydantic models in `src/models/transcript.py` for new data structures
3. **Error Handling**: Use `ToolError` for user-facing errors, especially for YouTube API failures
4. **Video ID Handling**: Support both video IDs and full YouTube URLs using `extract_video_id()`
5. **Testing**: Test tools with various video types (public, private, no transcripts, different languages)
6. **Language Support**: Handle both manually created and auto-generated transcripts

## Environment Variables

Key configuration variables:
```bash
YT_TRANSCRIPT_SERVER_PORT=8080    # Server port (default: 8080)
YT_TRANSCRIPT_SERVER_HOST=0.0.0.0 # Server host (default: 0.0.0.0)
YT_TRANSCRIPT_DEBUG=false         # Debug mode
```

## MCP Client Configuration

For streamable HTTP transport, add to your MCP client:

```json
{
  "yttranscript": {
    "command": "uvicorn",
    "args": [
      "src.server:app",
      "--host", "0.0.0.0", 
      "--port", "8080"
    ],
    "cwd": "/path/to/yttranscript_mcp"
  }
}
```

For stdio transport (legacy):
```json
{
  "yttranscript": {
    "command": "uv",
    "args": [
      "run",
      "--directory", "/path/to/yttranscript_mcp",
      "src/server.py"
    ]
  }
}
```

## Configuration Patterns

### Command-Line Arguments
```python
import argparse

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Your MCP Server')
    parser.add_argument('--api-key', help='API Key')
    parser.add_argument('--config-param', help='Configuration parameter')
    return parser.parse_args()

def main():
    """Main entry point for the MCP server."""
    args = parse_arguments()
    from src.config.settings import initialize_config
    initialize_config(api_key=args.api_key, config_param=args.config_param)
    mcp.run()

if __name__ == "__main__":
    main()
```

### Flexible Configuration Pattern
```python
# settings.py
import os
from dotenv import load_dotenv

load_dotenv()

# Global variables that can be set by command-line arguments
API_KEY = None
CONFIG_PARAM = None

def initialize_config(api_key=None, config_param=None):
    """Initialize configuration with command-line arguments or environment variables."""
    global API_KEY, CONFIG_PARAM
    
    # Use command-line arguments if provided, otherwise fall back to environment variables
    API_KEY = api_key or os.getenv('API_KEY')
    CONFIG_PARAM = config_param or os.getenv('CONFIG_PARAM')
    
    if not API_KEY:
        raise ValueError("API key must be provided via --api-key argument or API_KEY environment variable")
```

### Configuration Import Timing
**Important**: Import configuration modules inside tool functions to avoid timing issues:

```python
# WRONG - imports at module level before config is initialized
from src.config.settings import API_KEY

@mcp.tool()
async def my_tool():
    # API_KEY will be None here
    pass

# CORRECT - import inside function after config is set
@mcp.tool()
async def my_tool():
    from src.config.settings import API_KEY  # Gets current value
    # API_KEY has correct value here
```

### Server Configuration Example
```bash
# Run with custom settings
python src/server.py --port 3000 --host localhost --debug

# Or with uvicorn for production
uvicorn src.server:app --host 0.0.0.0 --port 8080 --workers 4
```

## Troubleshooting

### ✅ HTTP 429 Rate Limiting Issues - RESOLVED (September 2025)

**Previous Issue (Now Fixed):**
```
429 Client Error: Too Many Requests for url: 
https://www.youtube.com/api/timedtext?v=VIDEO_ID&...
```

**✅ CLI Migration Solution:**
- **Root Cause**: Direct HTTP requests to YouTube's subtitle URLs were being blocked
- **Fix**: Migrated to pure yt-dlp CLI subprocess execution using `--write-auto-subs`
- **Result**: No more HTTP 429 errors - CLI bypasses YouTube's anti-bot detection
- **Performance**: 2-5 seconds per transcript extraction
- **Reliability**: Consistent transcript fetching without rate limiting

**Current Status**: All tools now use CLI backend and are not subject to previous HTTP rate limiting issues.

### YouTube Transcript Specific Issues

- **"No transcript available"**: Video may have transcripts disabled, be private, or have restricted access
- **"Video unavailable"**: Check video ID format and ensure video exists and is public
- **Language not found**: Use `get_available_languages` to see what's available (this tool is most reliable)
- **Empty transcript**: Some videos may have transcripts but no actual content

### General MCP Issues

- **Tool not found**: Check tool is registered with `@mcp.tool()` decorator in `transcript_tools.py`
- **Validation errors**: Verify video ID is 11 characters and matches YouTube format
- **Connection issues**: Verify server is running on correct port (8000 by default)
- **Testing failures**: Use `mcp tools --server-logs python src/server.py` to see detailed errors
- **Build wheel errors**: Ensure `[tool.hatch.build.targets.wheel]` and `packages = ["src"]` in pyproject.toml
- **Import errors**: Run `uv pip install -e .` to install dependencies

### Transport Issues

- **Streamable HTTP not working**: Ensure uvicorn is installed and server is running with `uvicorn src.server:app`
- **STDIO transport issues**: Use `python src/server.py` for direct execution

## Testing Strategy

### Recommended Testing Approach

1. **Start with tool discovery**: `mcp tools .venv/bin/python src/server.py`
2. **Test language detection**: `mcp call get_available_languages --params '{"video_id":"VIDEO_ID"}'` 
3. **Test transcript fetching**: `mcp call get_transcript --params '{"video_id":"VIDEO_ID"}'`
4. **Use multiple test videos**: YouTube API issues may affect some videos but not others

### Reliable Test Videos

Try these videos known to work with YouTube's transcript API:
- **jNQXAC9IVRw** (Me at the zoo - first YouTube video)
- **9bZkp7q19f0** (Gangnam Style - popular video)
- **Various recent videos with auto-generated subtitles**

### When Transcript Fetching Fails

- ✅ **Tool discovery should always work**
- ✅ **Language detection (`get_available_languages`) is usually reliable**
- ⚠️ **Transcript fetching may fail due to YouTube API issues**
- 🔄 **Try different videos or wait for API stabilization**