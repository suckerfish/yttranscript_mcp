#!/usr/bin/env python3
"""
Direct test of the MCP server functionality
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from tools.transcript_tools import extract_video_id, fetch_subtitle_content


async def test_basic_extraction():
    """Test basic video ID extraction and subtitle fetching."""
    print("🧪 Testing Basic YouTube Transcript Extraction")
    print("=" * 60)
    
    # Test video ID extraction
    test_cases = [
        'jNQXAC9IVRw',  # Direct video ID
        'https://www.youtube.com/watch?v=jNQXAC9IVRw',  # Full URL
        'https://youtu.be/jNQXAC9IVRw'  # Short URL
    ]
    
    print("\n📋 Testing Video ID Extraction:")
    for test_case in test_cases:
        try:
            video_id = extract_video_id(test_case)
            print(f"  ✅ {test_case[:50]} → {video_id}")
        except Exception as e:
            print(f"  ❌ {test_case[:50]} → {e}")
    
    # Test actual transcript fetching
    print("\n📥 Testing Transcript Fetching:")
    test_video = 'jNQXAC9IVRw'  # "Me at the zoo" - first YouTube video
    
    try:
        entries, lang_code, lang_name, is_generated = fetch_subtitle_content(test_video)
        print(f"  ✅ Video: {test_video}")
        print(f"     Language: {lang_code} ({lang_name})")
        print(f"     Generated: {is_generated}")
        print(f"     Entries: {len(entries)}")
        
        if entries:
            print(f"     First entry: [{entries[0].start:.1f}s] {entries[0].text[:100]}...")
            print(f"     Last entry: [{entries[-1].start:.1f}s] {entries[-1].text[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Failed to fetch transcript: {e}")
        return False


async def test_tools_registration():
    """Test that tools are properly registered."""
    print("\n🔧 Testing Tool Registration:")
    
    try:
        # Import the server
        from server import mcp
        
        # Get tools info
        tools = mcp._tools
        print(f"  ✅ Server created successfully")
        print(f"     Registered tools: {len(tools)}")
        
        for tool_name in tools:
            print(f"     - {tool_name}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Failed to import server: {e}")
        return False


async def main():
    """Main test function."""
    print("🚀 YouTube Transcript MCP Server Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test basic extraction
    result1 = await test_basic_extraction()
    results.append(("Basic Extraction", result1))
    
    # Test tools registration
    result2 = await test_tools_registration()
    results.append(("Tools Registration", result2))
    
    # Summary
    print("\n📊 Test Results Summary:")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! MCP server is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)