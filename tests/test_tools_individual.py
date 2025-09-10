#!/usr/bin/env python3
"""
Individual test of each MCP tool
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

# Import the server and extract the tools
from server import mcp

# Test class to simulate MCP tool decorator
class MockMCP:
    def __init__(self):
        self.tools = {}
    
    def tool(self):
        def decorator(func):
            self.tools[func.__name__] = func
            return func
        return decorator

async def test_individual_tools():
    """Test each tool individually."""
    print("🔧 Testing Individual MCP Tools")
    print("=" * 60)
    
    # Register tools with mock MCP to extract them
    mock_mcp = MockMCP()
    
    from tools.transcript_tools import register_transcript_tools
    register_transcript_tools(mock_mcp)
    
    print(f"Registered tools: {list(mock_mcp.tools.keys())}")
    
    # Test parameters
    test_video = 'jNQXAC9IVRw'  # "Me at the zoo"
    
    results = []
    
    # Test get_transcript
    print(f"\n📥 Testing get_transcript with video: {test_video}")
    try:
        get_transcript = mock_mcp.tools['get_transcript']
        result = await get_transcript(video_id=test_video)
        
        print(f"  ✅ get_transcript successful")
        print(f"     Video ID: {result.video_id}")
        print(f"     Language: {result.language_code} ({result.language_name})")
        print(f"     Generated: {result.is_generated}")
        print(f"     Entries: {len(result.transcript)}")
        print(f"     Duration: {result.total_duration:.1f}s")
        print(f"     Words: {result.word_count}")
        
        results.append(("get_transcript", True))
        
    except Exception as e:
        print(f"  ❌ get_transcript failed: {e}")
        results.append(("get_transcript", False))
    
    # Test get_available_languages
    print(f"\n🌐 Testing get_available_languages with video: {test_video}")
    try:
        get_available_languages = mock_mcp.tools['get_available_languages']
        languages = await get_available_languages(video_id=test_video)
        
        print(f"  ✅ get_available_languages successful")
        print(f"     Available languages: {len(languages)}")
        
        for lang in languages[:5]:  # Show first 5
            print(f"     - {lang.language_code}: {lang.language_name} (generated: {lang.is_generated})")
        
        if len(languages) > 5:
            print(f"     ... and {len(languages) - 5} more")
        
        results.append(("get_available_languages", True))
        
    except Exception as e:
        print(f"  ❌ get_available_languages failed: {e}")
        results.append(("get_available_languages", False))
    
    # Test search_transcript
    print(f"\n🔍 Testing search_transcript with video: {test_video}")
    try:
        search_transcript = mock_mcp.tools['search_transcript']
        search_result = await search_transcript(video_id=test_video, query="elephant")
        
        print(f"  ✅ search_transcript successful")
        print(f"     Query: 'elephant'")
        print(f"     Matches: {search_result.total_matches}")
        
        for i, match in enumerate(search_result.results[:3]):  # Show first 3
            print(f"     Match {i+1}: [{match.timestamp_formatted}] {match.match_text}")
            print(f"               Context: ...{match.context_before} [{match.match_text}] {match.context_after}...")
        
        results.append(("search_transcript", True))
        
    except Exception as e:
        print(f"  ❌ search_transcript failed: {e}")
        results.append(("search_transcript", False))
    
    # Test get_transcript_summary
    print(f"\n📊 Testing get_transcript_summary with video: {test_video}")
    try:
        get_transcript_summary = mock_mcp.tools['get_transcript_summary']
        summary = await get_transcript_summary(video_id=test_video)
        
        print(f"  ✅ get_transcript_summary successful")
        print(f"     Video ID: {summary['video_id']}")
        print(f"     Language: {summary['language_code']} ({summary['language_name']})")
        print(f"     Duration: {summary['statistics']['total_duration_formatted']}")
        print(f"     Words: {summary['statistics']['total_words']}")
        print(f"     Reading time: {summary['statistics']['estimated_reading_time_minutes']} min")
        print(f"     Sample text: {summary['sample_text'][:100]}...")
        
        results.append(("get_transcript_summary", True))
        
    except Exception as e:
        print(f"  ❌ get_transcript_summary failed: {e}")
        results.append(("get_transcript_summary", False))
    
    # Summary
    print("\n📊 Individual Tool Test Results:")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for tool_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {tool_name}")
    
    print(f"\nOverall: {passed}/{total} tools working correctly")
    
    return passed == total


async def main():
    """Main test function."""
    success = await test_individual_tools()
    
    if success:
        print("\n🎉 All tools are working correctly!")
        print("The MCP server implementation is ready for use.")
    else:
        print("\n⚠️  Some tools failed. Check the output above for details.")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)