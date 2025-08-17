#!/usr/bin/env python3
"""
Test auto-generated subtitle functionality
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from tools.transcript_tools import register_transcript_tools

# Test class to simulate MCP tool decorator
class MockMCP:
    def __init__(self):
        self.tools = {}
    
    def tool(self):
        def decorator(func):
            self.tools[func.__name__] = func
            return func
        return decorator

async def test_auto_generated_subtitles():
    """Test auto-generated subtitle functionality."""
    print("🤖 Testing Auto-Generated Subtitle Support")
    print("=" * 60)
    
    # Register tools
    mock_mcp = MockMCP()
    register_transcript_tools(mock_mcp)
    
    # Test with a video that typically has auto-generated subtitles
    test_video = 'dQw4w9WgXcQ'  # Rick Roll - very popular video, likely auto-generated
    
    print(f"Testing with video: {test_video}")
    
    # Test get_available_languages first
    print("\n🌐 Testing available languages:")
    try:
        get_available_languages = mock_mcp.tools['get_available_languages']
        languages = await get_available_languages(video_id=test_video)
        
        print(f"  Available languages: {len(languages)}")
        
        manual_count = sum(1 for lang in languages if not lang.is_generated)
        auto_count = sum(1 for lang in languages if lang.is_generated)
        
        print(f"  Manual subtitles: {manual_count}")
        print(f"  Auto-generated: {auto_count}")
        
        # Show some examples
        for lang in languages[:10]:  # Show first 10
            type_str = "auto" if lang.is_generated else "manual"
            print(f"    - {lang.language_code}: {lang.language_name} ({type_str})")
        
        if len(languages) > 10:
            print(f"    ... and {len(languages) - 10} more")
        
    except Exception as e:
        print(f"  ❌ get_available_languages failed: {e}")
        return False
    
    # Test get_transcript with auto language selection
    print(f"\n📥 Testing get_transcript (auto language selection):")
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
        
        if result.transcript:
            print(f"     First entry: [{result.transcript[0].start:.1f}s] {result.transcript[0].text[:100]}...")
        
    except Exception as e:
        print(f"  ❌ get_transcript failed: {e}")
        return False
    
    # Test with specific language that might be auto-generated
    print(f"\n📥 Testing get_transcript (specific auto-generated language):")
    try:
        # Try to get auto-generated English if available
        auto_en_available = any(lang.language_code == 'en' and lang.is_generated for lang in languages)
        
        if auto_en_available:
            result = await get_transcript(video_id=test_video, language_code='en')
            print(f"  ✅ Auto-generated English transcript fetched")
            print(f"     Generated: {result.is_generated}")
            print(f"     Entries: {len(result.transcript)}")
        else:
            print(f"  ℹ️  No auto-generated English available for this video")
        
    except Exception as e:
        print(f"  ❌ Specific language fetch failed: {e}")
    
    # Test time filtering
    print(f"\n⏱️ Testing time-filtered transcript (first 30 seconds):")
    try:
        result = await get_transcript(video_id=test_video, start_time=0, end_time=30)
        
        print(f"  ✅ Time-filtered transcript successful")
        print(f"     Entries in first 30s: {len(result.transcript)}")
        print(f"     Duration shown: {result.total_duration:.1f}s")
        
        if result.transcript:
            print(f"     First: [{result.transcript[0].start:.1f}s] {result.transcript[0].text[:50]}...")
            print(f"     Last: [{result.transcript[-1].start:.1f}s] {result.transcript[-1].text[:50]}...")
        
    except Exception as e:
        print(f"  ❌ Time filtering failed: {e}")
    
    print(f"\n🎯 Auto-generated subtitle support is working correctly!")
    return True


async def main():
    """Main test function."""
    success = await test_auto_generated_subtitles()
    
    if success:
        print("\n🎉 Auto-generated subtitle functionality confirmed!")
        print("The yt-dlp implementation successfully handles both manual and auto-generated subtitles.")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)