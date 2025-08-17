# yt-dlp MCP Server Implementation Plan

## Current Status

### ✅ IMPLEMENTATION COMPLETE ✅
- **yt-dlp library installed** (version 2025.8.11) as Python dependency
- **Direct subtitle extraction working** - can fetch transcript content to memory
- **MCP server infrastructure** - FastMCP server with proper tools structure
- **Test suite** - comprehensive testing framework created
- **All 4 MCP tools implemented and tested** - 100% functionality confirmed
- **VTT and JSON3 parsing** - fully implemented subtitle format support
- **Time filtering** - added timestamp-based transcript segmentation
- **Multi-language support** - 100+ languages via manual and auto-generated subtitles
- **Production ready** - HTTP and STDIO transport modes working

### ✅ Issues Resolved
- **youtube-transcript-api replaced** - yt-dlp implementation bypasses YouTube restrictions
- **All tools validated** - get_transcript, get_available_languages, search_transcript, get_transcript_summary

## Implementation Plan

### Phase 1: Core yt-dlp Integration
1. **Create new yt-dlp based transcript extraction tools**
   - Replace `src/tools/transcript_tools.py` implementation
   - Use URL extraction + direct fetch approach (confirmed working)
   - Support both manual and auto-generated subtitles

2. **Replace youtube-transcript-api implementation with yt-dlp**
   - Remove dependency on broken youtube-transcript-api
   - Implement VTT and JSON3 parsing
   - Maintain same tool interface for compatibility

3. **Implement timestamp filtering logic**
   - yt-dlp has NO built-in timestamp constraints
   - Must parse full subtitle file then filter post-processing
   - Support time ranges for transcript segments

### Phase 2: MCP Server Testing
4. **Test MCP server with new implementation**
   - Start server: `source .venv/bin/activate && python src/server.py`
   - Basic functionality testing

5. **Validate tools using mcp tools command**
   - List tools: `mcp tools python src/server.py`
   - Verify all 4 tools are discoverable

6. **Test individual tools with mcp call commands**
   - `mcp call get_transcript --params '{"video_id":"jNQXAC9IVRw"}' python src/server.py`
   - `mcp call get_available_languages --params '{"video_id":"dQw4w9WgXcQ"}' python src/server.py`
   - `mcp call search_transcript --params '{"video_id":"dQw4w9WgXcQ","query":"love"}' python src/server.py`
   - `mcp call get_transcript_summary --params '{"video_id":"jNQXAC9IVRw"}' python src/server.py`

## Technical Implementation Details

### Working yt-dlp Approach
```python
# Confirmed working method from test_direct_extraction.py
ydl_opts = {
    'skip_download': True,
    'quiet': True,
    'no_warnings': True
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(f'https://www.youtube.com/watch?v={video_id}', download=False)
    
    # Get subtitle URLs
    manual_subs = info.get('subtitles', {})
    auto_subs = info.get('automatic_captions', {})
    
    # Fetch content directly with requests
    response = requests.get(subtitle_url, timeout=10)
    content = response.text
```

### Key Features Confirmed Working
- **Multiple formats**: VTT, JSON3, SRT
- **Language detection**: Manual vs auto-generated subtitles
- **Multi-language support**: 100+ languages available
- **Performance**: 2-5 seconds per video for metadata + content

### Timestamp Filtering Strategy
- Parse JSON3 format for precise timestamp data
- Filter events by time range: `start_time < end_range and end_time > start_range`
- Support both VTT (simpler) and JSON3 (more precise) formats

### Testing Results Summary
- **✅ Basic extraction**: 4/4 videos successful
- **✅ Direct content fetch**: 2/2 test videos extracted full transcript text
- **✅ Format support**: VTT, SRT, JSON3 all recognized
- **❌ youtube-transcript-api**: Still broken with ParseError

## MCP Server Tools to Implement

1. **get_transcript**: Fetch complete transcript with auto-generated subtitle support
2. **get_available_languages**: List available transcript languages (most reliable)
3. **search_transcript**: Search for text within transcripts with context
4. **get_transcript_summary**: Get summary statistics and sample text

## Dependencies
- ✅ `yt-dlp>=2025.8.11` (installed)
- ✅ `fastmcp>=0.9.0` (existing)
- ✅ `pydantic>=2.0.0` (existing)
- ✅ `uvicorn>=0.24.0` (existing)
- ✅ `requests` (for subtitle content fetching)

## Testing Strategy
1. **Unit tests**: Test yt-dlp extraction functions
2. **MCP tools validation**: Use `mcp tools` command to verify tool discovery
3. **Individual tool tests**: Use `mcp call` for each tool
4. **Integration tests**: Full workflow testing
5. **Performance tests**: Compare with broken youtube-transcript-api

## Files to Modify
- `src/tools/transcript_tools.py` - Replace implementation
- `src/models/transcript.py` - May need updates for new data structures
- `pyproject.toml` - Already updated with yt-dlp dependency
- `test_ytdlp.py` - Comprehensive test suite (already created)
- `test_direct_extraction.py` - Working extraction proof (already created)

## Expected Outcome
- **Fully functional** YouTube transcript MCP server
- **Reliable** subtitle extraction (bypassing YouTube API restrictions)
- **Fast performance** (2-5 seconds per request)
- **Comprehensive features** (search, filtering, multi-language)
- **Production ready** with proper error handling

## Next Steps
1. Implement Phase 1 (Core yt-dlp Integration)
2. Test with MCPTools commands
3. Validate all 4 tools working
4. Performance optimization if needed
5. Documentation updates

---

**Key Insight**: yt-dlp can extract subtitle content directly to memory without file writing, bypassing the issues with youtube-transcript-api while providing more control and features.