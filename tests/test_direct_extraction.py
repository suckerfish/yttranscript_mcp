#!/usr/bin/env python3
"""
Test direct subtitle content extraction from yt-dlp without file writing.
Focus on getting actual transcript text into memory.
"""

import sys
import json
import requests
from typing import Dict, List, Any, Optional

try:
    import yt_dlp
except ImportError:
    print("❌ yt-dlp not installed. Run: uv add yt-dlp")
    sys.exit(1)


def test_direct_subtitle_extraction(video_id: str) -> Dict[str, Any]:
    """Test direct subtitle extraction without writing files."""
    print(f"\n🔍 Testing direct extraction for video: {video_id}")
    print("=" * 60)
    
    result = {
        'video_id': video_id,
        'success': False,
        'method_results': {}
    }
    
    # Method 1: Extract subtitle URLs and fetch content directly
    print("\n📥 Method 1: Extract subtitle URLs and fetch content")
    try:
        ydl_opts = {
            'skip_download': True,
            'quiet': True,
            'no_warnings': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f'https://www.youtube.com/watch?v={video_id}', download=False)
            
            # Check for manual subtitles first
            manual_subs = info.get('subtitles', {})
            auto_subs = info.get('automatic_captions', {})
            
            print(f"  Manual subtitles available: {list(manual_subs.keys())}")
            print(f"  Auto captions available: {list(auto_subs.keys())[:10]}{'...' if len(auto_subs) > 10 else ''}")
            
            # Try to get English subtitles (manual first, then auto)
            subtitle_data = None
            subtitle_type = None
            
            if 'en' in manual_subs:
                subtitle_data = manual_subs['en']
                subtitle_type = 'manual'
                print("  📝 Using manual English subtitles")
            elif 'en' in auto_subs:
                subtitle_data = auto_subs['en']
                subtitle_type = 'auto'
                print("  🤖 Using auto-generated English subtitles")
            else:
                print("  ❌ No English subtitles found")
                return result
            
            # Find a suitable format (prefer vtt, then json3)
            subtitle_url = None
            subtitle_format = None
            
            for entry in subtitle_data:
                if entry.get('ext') == 'vtt':
                    subtitle_url = entry.get('url')
                    subtitle_format = 'vtt'
                    break
                elif entry.get('ext') == 'json3':
                    subtitle_url = entry.get('url')
                    subtitle_format = 'json3'
            
            if not subtitle_url:
                # Fallback to first available format
                if subtitle_data:
                    subtitle_url = subtitle_data[0].get('url')
                    subtitle_format = subtitle_data[0].get('ext', 'unknown')
            
            if subtitle_url:
                print(f"  🌐 Found {subtitle_format} subtitle URL: {subtitle_url[:100]}...")
                
                # Fetch the subtitle content
                response = requests.get(subtitle_url, timeout=10)
                response.raise_for_status()
                
                content = response.text
                print(f"  ✅ Successfully fetched {len(content)} characters of subtitle content")
                
                # Parse and extract some sample text
                if subtitle_format == 'vtt':
                    # Extract text from VTT format
                    lines = content.split('\n')
                    text_lines = []
                    for line in lines:
                        line = line.strip()
                        # Skip VTT headers, timestamps, and empty lines
                        if (line and 
                            not line.startswith('WEBVTT') and 
                            not line.startswith('NOTE') and
                            '-->' not in line and
                            not line.startswith('<')):
                            text_lines.append(line)
                    
                    sample_text = ' '.join(text_lines[:20])  # First 20 text segments
                    print(f"  📄 Sample VTT text: {sample_text[:200]}...")
                    
                elif subtitle_format == 'json3':
                    # Parse JSON3 format
                    subtitle_json = json.loads(content)
                    events = subtitle_json.get('events', [])
                    
                    text_segments = []
                    for event in events[:10]:  # First 10 events
                        segments = event.get('segs', [])
                        for seg in segments:
                            text = seg.get('utf8', '').strip()
                            if text:
                                text_segments.append(text)
                    
                    sample_text = ' '.join(text_segments)
                    print(f"  📄 Sample JSON3 text: {sample_text[:200]}...")
                
                result['method_results']['url_fetch'] = {
                    'success': True,
                    'subtitle_type': subtitle_type,
                    'format': subtitle_format,
                    'content_length': len(content),
                    'sample_text': sample_text[:500] if 'sample_text' in locals() else 'Could not parse sample',
                    'url': subtitle_url
                }
                result['success'] = True
                
            else:
                print("  ❌ No subtitle URL found")
                result['method_results']['url_fetch'] = {
                    'success': False,
                    'error': 'No subtitle URL found'
                }
    
    except Exception as e:
        print(f"  ❌ Method 1 failed: {e}")
        result['method_results']['url_fetch'] = {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }
    
    # Method 2: Try using yt-dlp's built-in subtitle processing
    print("\n🔧 Method 2: yt-dlp built-in subtitle processing")
    try:
        ydl_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
            'subtitlesformat': 'json3',
            'quiet': True,
            'no_warnings': True,
            # Try to get content without writing to disk
            'logtostderr': False,
        }
        
        # Use a custom output template that might give us access to subtitle data
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Try to extract and see if we can intercept subtitle data
            info = ydl.extract_info(f'https://www.youtube.com/watch?v={video_id}', download=False)
            
            # Check if subtitle content is available in the info dict
            if 'requested_subtitles' in info:
                print("  📋 Found requested_subtitles in info dict")
                requested = info['requested_subtitles']
                for lang, sub_info in requested.items():
                    print(f"    Language: {lang}")
                    print(f"    URL: {sub_info.get('url', 'No URL')[:100]}...")
                    if 'data' in sub_info:
                        print(f"    Data available: {len(sub_info['data'])} chars")
                        result['method_results']['builtin'] = {
                            'success': True,
                            'language': lang,
                            'data_length': len(sub_info['data']),
                            'sample': sub_info['data'][:500]
                        }
                        result['success'] = True
            else:
                print("  ❌ No requested_subtitles found in info dict")
                result['method_results']['builtin'] = {
                    'success': False,
                    'error': 'No requested_subtitles in info dict'
                }
    
    except Exception as e:
        print(f"  ❌ Method 2 failed: {e}")
        result['method_results']['builtin'] = {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }
    
    return result


def main():
    """Test direct subtitle extraction on multiple videos."""
    print("🚀 Testing Direct Subtitle Extraction with yt-dlp")
    print("=" * 60)
    
    test_videos = [
        'jNQXAC9IVRw',  # Me at the zoo (short, likely has subtitles)
        'dQw4w9WgXcQ',  # Rick Roll (popular, manual subtitles)
    ]
    
    results = {}
    
    for video_id in test_videos:
        result = test_direct_subtitle_extraction(video_id)
        results[video_id] = result
        
        if result['success']:
            print(f"\n✅ SUCCESS for {video_id}")
        else:
            print(f"\n❌ FAILED for {video_id}")
    
    # Summary
    print("\n📊 SUMMARY")
    print("=" * 60)
    
    successful_extractions = sum(1 for r in results.values() if r['success'])
    total_tests = len(results)
    
    print(f"Successful extractions: {successful_extractions}/{total_tests}")
    
    for video_id, result in results.items():
        if result['success']:
            print(f"\n✅ {video_id}:")
            for method, method_result in result['method_results'].items():
                if method_result.get('success'):
                    print(f"  📝 {method}: {method_result.get('subtitle_type', 'unknown')} "
                          f"({method_result.get('format', 'unknown')}) - "
                          f"{method_result.get('content_length', 0)} chars")
    
    if successful_extractions > 0:
        print(f"\n🎯 CONCLUSION: yt-dlp CAN extract subtitle content directly!")
        print("   Recommendation: Use URL fetching method for MCP server implementation")
    else:
        print(f"\n❌ CONCLUSION: Direct subtitle extraction not working")
    
    return results


if __name__ == "__main__":
    results = main()