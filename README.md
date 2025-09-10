# YouTube Transcript MCP Server

A **production-ready** Model Context Protocol (MCP) server that provides YouTube transcript fetching capabilities using **yt-dlp CLI** for reliable subtitle extraction. Bypasses YouTube's rate limiting through CLI-based implementation.

## Status: Production Ready ✅

**Implementation:** Full CLI migration complete (September 2025)
- ✅ **CLI-Based:** Uses yt-dlp subprocess to avoid HTTP rate limiting
- ✅ **Universal Compatibility:** Time parameters work across all MCP clients
- ✅ **Advanced Analytics:** Enhanced transcript summary with content analysis
- ✅ **Multi-Language:** 100+ languages with auto-generated and manual transcripts

## Features

- **Fetch transcripts** from YouTube videos with metadata and timestamps
- **Time filtering** - extract specific segments by start/end times
- **Search functionality** - find text within transcripts with context  
- **Advanced analytics** - speaking pace, filler words, engagement metrics, top words
- **Language detection** - list available transcript languages
- **Universal format support** - handles both video IDs and full YouTube URLs
- **Dual transport** - STDIO and HTTP transport modes
- **Docker support** - containerized deployment with health checks

## Installation

### Quick Start
```bash
# Install dependencies
uv pip install -e .

# Run server (STDIO mode)
python src/server.py

# Run server (HTTP mode)
uvicorn src.server:app --host 0.0.0.0 --port 8080
```

### Docker (Recommended)
```bash
# Build and run
docker build -t yttranscript-mcp .
docker run -d -p 8080:8080 yttranscript-mcp

# Or use docker-compose
docker-compose up -d yttranscript-mcp

# Health check
curl http://localhost:8080/health
```

## Usage

### Available Tools

1. **get_transcript** - Fetch video transcripts with optional time filtering
2. **search_transcript** - Search for specific text within transcripts  
3. **get_transcript_summary** - Advanced analytics and content insights
4. **get_available_languages** - List available transcript languages

### Testing Commands

```bash
# Discover tools
mcp tools .venv/bin/python src/server.py

# Basic transcript
mcp call get_transcript --params '{"video_id":"jNQXAC9IVRw"}' .venv/bin/python src/server.py

# Time-filtered transcript
mcp call get_transcript --params '{"video_id":"jNQXAC9IVRw", "start_time": 10, "end_time": 60}' .venv/bin/python src/server.py

# Search within transcript
mcp call search_transcript --params '{"video_id":"jNQXAC9IVRw", "query":"example"}' .venv/bin/python src/server.py

# Advanced analytics
mcp call get_transcript_summary --params '{"video_id":"jNQXAC9IVRw"}' .venv/bin/python src/server.py

# Available languages
mcp call get_available_languages --params '{"video_id":"jNQXAC9IVRw"}' .venv/bin/python src/server.py
```

## MCP Client Configuration

### HTTP Transport (Production)
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

### STDIO Transport (Development)
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

## Key Features

### Universal Parameter Compatibility
Time filtering parameters accept multiple formats:
- Integers: `{"start_time": 10}`
- Floats: `{"start_time": 10.5}` 
- Strings: `{"start_time": "10"}`
- Nulls: `{"start_time": null}` or `{"start_time": "null"}`

### Advanced Analytics
The `get_transcript_summary` tool provides:
- **Speaking pace analysis** (words per minute with descriptive labels)
- **Filler word detection** (um, uh, like, etc.) with percentages
- **Content indicators** (conversational, formal, high energy)
- **Top frequent words** (excluding stop words)
- **Engagement metrics** (questions, exclamations)
- **Reading time estimates** at multiple speeds

### CLI Implementation Benefits
- **No rate limiting** - bypasses YouTube's HTTP restrictions
- **Reliable extraction** - uses yt-dlp's robust parsing
- **Better error handling** - clear error messages for various failure modes
- **Format flexibility** - handles VTT, JSON3, and other subtitle formats

## Configuration

### Environment Variables
```bash
YT_TRANSCRIPT_SERVER_PORT=8080    # Server port (default: 8080)
YT_TRANSCRIPT_SERVER_HOST=0.0.0.0 # Server host (default: 0.0.0.0)
YT_TRANSCRIPT_DEBUG=false         # Debug mode
```

### Docker Environment
```bash
# Production
docker run -e YT_TRANSCRIPT_SERVER_PORT=8080 yttranscript-mcp

# Development with auto-reload  
docker-compose --profile dev up yttranscript-mcp-dev
```

## Dependencies

- **fastmcp>=0.9.0** - MCP server framework
- **yt-dlp>=2025.8.11** - YouTube transcript extraction via CLI
- **pydantic>=2.0.0** - Data validation and models
- **uvicorn>=0.24.0** - ASGI server for HTTP transport

This project uses `uv` for package management.

## Troubleshooting

- **Tool not found**: Verify `@mcp.tool()` decorator in tool definitions
- **Validation errors**: Video IDs must be 11 characters, time values must be non-negative
- **Time filtering issues**: Parameters accept multiple formats (int/float/string/null)
- **Transport issues**: Use `uvicorn` for HTTP mode, `python src/server.py` for STDIO
- **No transcript available**: Check with `get_available_languages` first

## License

This project is open source and available under the [MIT License](LICENSE).