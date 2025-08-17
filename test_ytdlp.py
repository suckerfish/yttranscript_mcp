#!/usr/bin/env python3
"""
Comprehensive test suite for yt-dlp transcript extraction capabilities.
Tests various video types, formats, and filtering options.
"""

import sys
import json
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import time

try:
    import yt_dlp
    from yt_dlp.utils import DownloadError
except ImportError:
    print("❌ yt-dlp not installed. Run: uv add yt-dlp")
    sys.exit(1)


class YtDlpTranscriptTester:
    """Comprehensive tester for yt-dlp transcript extraction capabilities."""
    
    def __init__(self):
        self.test_videos = [
            {
                'id': 'jNQXAC9IVRw',
                'title': 'Me at the zoo (First YouTube video)',
                'description': 'Very short video, likely has transcripts'
            },
            {
                'id': 'dQw4w9WgXcQ', 
                'title': 'Rick Astley - Never Gonna Give You Up',
                'description': 'Popular music video with lyrics'
            },
            {
                'id': '9bZkp7q19f0',
                'title': 'PSY - Gangnam Style',
                'description': 'Most viewed video, multilingual'
            },
            {
                'id': 'KeRsFAiJGww',
                'title': 'Test video',
                'description': 'Generic test case'
            }
        ]
        
        # Test results storage
        self.results = {
            'basic_extraction': {},
            'format_tests': {},
            'language_tests': {},
            'filtering_tests': {},
            'performance_tests': {}
        }
    
    def test_basic_extraction(self) -> Dict[str, Any]:
        """Test basic transcript extraction without any filters."""
        print("\n🔍 Testing Basic Transcript Extraction")
        print("=" * 50)
        
        results = {}
        
        for video in self.test_videos:
            video_id = video['id']
            print(f"\nTesting video: {video['title']} ({video_id})")
            
            # Basic extraction options
            ydl_opts = {
                'skip_download': True,
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['en'],
                'subtitlesformat': 'vtt',
                'quiet': True,
                'no_warnings': True
            }
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    start_time = time.time()
                    info = ydl.extract_info(f'https://www.youtube.com/watch?v={video_id}', download=False)
                    extraction_time = time.time() - start_time
                    
                    # Check available subtitles
                    subtitles = info.get('subtitles', {})
                    automatic_captions = info.get('automatic_captions', {})
                    
                    result = {
                        'success': True,
                        'extraction_time': extraction_time,
                        'manual_subtitles': list(subtitles.keys()),
                        'automatic_captions': list(automatic_captions.keys()),
                        'video_duration': info.get('duration', 0),
                        'video_title': info.get('title', 'Unknown')
                    }
                    
                    print(f"  ✅ Success in {extraction_time:.2f}s")
                    print(f"     Manual subtitles: {result['manual_subtitles']}")
                    print(f"     Auto captions: {result['automatic_captions']}")
                    print(f"     Duration: {result['video_duration']}s")
                    
            except Exception as e:
                result = {
                    'success': False,
                    'error': str(e),
                    'error_type': type(e).__name__
                }
                print(f"  ❌ Failed: {e}")
            
            results[video_id] = result
        
        self.results['basic_extraction'] = results
        return results
    
    def test_subtitle_formats(self) -> Dict[str, Any]:
        """Test different subtitle formats (VTT, SRT, JSON)."""
        print("\n📄 Testing Subtitle Formats")
        print("=" * 50)
        
        results = {}
        formats_to_test = ['vtt', 'srt', 'json3']
        
        # Use first working video from basic test
        test_video_id = None
        for vid_id, result in self.results['basic_extraction'].items():
            if result.get('success') and (result.get('manual_subtitles') or result.get('automatic_captions')):
                test_video_id = vid_id
                break
        
        if not test_video_id:
            print("  ⚠️  No working video found from basic tests")
            return {}
        
        print(f"Testing formats with video: {test_video_id}")
        
        for fmt in formats_to_test:
            print(f"\n  Testing format: {fmt}")
            
            ydl_opts = {
                'skip_download': True,
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['en'],
                'subtitlesformat': fmt,
                'quiet': True,
                'no_warnings': True
            }
            
            try:
                with tempfile.TemporaryDirectory() as temp_dir:
                    ydl_opts['outtmpl'] = os.path.join(temp_dir, '%(id)s.%(ext)s')
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(f'https://www.youtube.com/watch?v={test_video_id}', download=False)
                        
                        # Check if subtitle files were created
                        subtitle_files = list(Path(temp_dir).glob(f'*{test_video_id}*.{fmt}'))
                        
                        result = {
                            'success': True,
                            'files_created': len(subtitle_files),
                            'file_paths': [str(f) for f in subtitle_files]
                        }
                        
                        # Try to read and analyze first file
                        if subtitle_files:
                            with open(subtitle_files[0], 'r', encoding='utf-8') as f:
                                content = f.read()
                                result['sample_content'] = content[:500] + ('...' if len(content) > 500 else '')
                                result['content_length'] = len(content)
                        
                        print(f"    ✅ Success: {len(subtitle_files)} files created")
                        
            except Exception as e:
                result = {
                    'success': False,
                    'error': str(e),
                    'error_type': type(e).__name__
                }
                print(f"    ❌ Failed: {e}")
            
            results[fmt] = result
        
        self.results['format_tests'] = results
        return results
    
    def test_language_support(self) -> Dict[str, Any]:
        """Test multi-language subtitle extraction."""
        print("\n🌍 Testing Language Support")
        print("=" * 50)
        
        results = {}
        
        # Use a video known to have multiple languages (Gangnam Style)
        test_video_id = '9bZkp7q19f0'
        
        print(f"Testing languages with: {test_video_id}")
        
        # First, discover all available languages
        ydl_opts = {
            'skip_download': True,
            'listsubtitles': True,
            'quiet': True,
            'no_warnings': True
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f'https://www.youtube.com/watch?v={test_video_id}', download=False)
                
                subtitles = info.get('subtitles', {})
                automatic_captions = info.get('automatic_captions', {})
                
                all_languages = set(subtitles.keys()) | set(automatic_captions.keys())
                
                print(f"  Available languages: {sorted(all_languages)}")
                
                # Test specific languages
                languages_to_test = ['en', 'es', 'fr', 'de', 'ko', 'ja']
                available_to_test = [lang for lang in languages_to_test if lang in all_languages]
                
                print(f"  Testing languages: {available_to_test}")
                
                for lang in available_to_test[:3]:  # Test first 3 to avoid too much output
                    print(f"\n    Testing language: {lang}")
                    
                    lang_opts = {
                        'skip_download': True,
                        'writesubtitles': True,
                        'writeautomaticsub': True,
                        'subtitleslangs': [lang],
                        'subtitlesformat': 'vtt',
                        'quiet': True,
                        'no_warnings': True
                    }
                    
                    try:
                        with tempfile.TemporaryDirectory() as temp_dir:
                            lang_opts['outtmpl'] = os.path.join(temp_dir, '%(id)s.%(ext)s')
                            
                            with yt_dlp.YoutubeDL(lang_opts) as lang_ydl:
                                lang_ydl.extract_info(f'https://www.youtube.com/watch?v={test_video_id}', download=False)
                                
                                subtitle_files = list(Path(temp_dir).glob('*.vtt'))
                                
                                if subtitle_files:
                                    with open(subtitle_files[0], 'r', encoding='utf-8') as f:
                                        content = f.read()
                                    
                                    results[lang] = {
                                        'success': True,
                                        'content_length': len(content),
                                        'sample': content[:200] + ('...' if len(content) > 200 else '')
                                    }
                                    print(f"      ✅ Success: {len(content)} chars")
                                else:
                                    results[lang] = {'success': False, 'error': 'No subtitle file created'}
                                    print(f"      ❌ No subtitle file created")
                                    
                    except Exception as e:
                        results[lang] = {
                            'success': False,
                            'error': str(e),
                            'error_type': type(e).__name__
                        }
                        print(f"      ❌ Failed: {e}")
                
                results['_metadata'] = {
                    'all_available_languages': sorted(all_languages),
                    'manual_subtitles': sorted(subtitles.keys()),
                    'automatic_captions': sorted(automatic_captions.keys())
                }
                
        except Exception as e:
            results = {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
            print(f"  ❌ Failed to get language info: {e}")
        
        self.results['language_tests'] = results
        return results
    
    def test_timestamp_filtering(self) -> Dict[str, Any]:
        """Test timestamp-based filtering and constraints."""
        print("\n⏱️  Testing Timestamp Filtering and Constraints")
        print("=" * 50)
        
        results = {}
        
        # Get a working video with decent length
        test_video_id = None
        for vid_id, result in self.results['basic_extraction'].items():
            if (result.get('success') and 
                result.get('video_duration', 0) > 60 and  # At least 1 minute
                (result.get('manual_subtitles') or result.get('automatic_captions'))):
                test_video_id = vid_id
                break
        
        if not test_video_id:
            print("  ⚠️  No suitable video found for timestamp testing")
            return {}
        
        video_duration = self.results['basic_extraction'][test_video_id].get('video_duration', 0)
        print(f"Testing with video: {test_video_id} (duration: {video_duration}s)")
        
        # Test different timestamp constraints
        test_cases = [
            {
                'name': 'First 30 seconds',
                'start': 0,
                'end': 30
            },
            {
                'name': 'Middle portion',
                'start': max(30, video_duration // 3),
                'end': min(video_duration - 30, 2 * video_duration // 3)
            },
            {
                'name': 'Last 30 seconds',
                'start': max(0, video_duration - 30),
                'end': video_duration
            }
        ]
        
        for test_case in test_cases:
            print(f"\n  Testing: {test_case['name']} ({test_case['start']}s - {test_case['end']}s)")
            
            # Note: yt-dlp doesn't have built-in subtitle time filtering
            # We'll need to extract full subtitles and filter post-processing
            ydl_opts = {
                'skip_download': True,
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['en'],
                'subtitlesformat': 'json3',  # JSON format for easier parsing
                'quiet': True,
                'no_warnings': True
            }
            
            try:
                with tempfile.TemporaryDirectory() as temp_dir:
                    ydl_opts['outtmpl'] = os.path.join(temp_dir, '%(id)s.%(ext)s')
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.extract_info(f'https://www.youtube.com/watch?v={test_video_id}', download=False)
                        
                        # Find JSON subtitle file
                        json_files = list(Path(temp_dir).glob('*.json'))
                        
                        if json_files:
                            with open(json_files[0], 'r', encoding='utf-8') as f:
                                subtitle_data = json.load(f)
                            
                            # Filter events by timestamp
                            events = subtitle_data.get('events', [])
                            filtered_events = []
                            
                            for event in events:
                                start_time = event.get('tStartMs', 0) / 1000.0
                                duration = event.get('dDurationMs', 0) / 1000.0
                                end_time = start_time + duration
                                
                                # Check if event overlaps with our time range
                                if (start_time < test_case['end'] and end_time > test_case['start']):
                                    filtered_events.append(event)
                            
                            # Extract text from filtered events
                            filtered_text = []
                            for event in filtered_events:
                                segments = event.get('segs', [])
                                for seg in segments:
                                    text = seg.get('utf8', '').strip()
                                    if text:
                                        filtered_text.append(text)
                            
                            results[test_case['name']] = {
                                'success': True,
                                'total_events': len(events),
                                'filtered_events': len(filtered_events),
                                'filtered_text_length': len(' '.join(filtered_text)),
                                'sample_text': ' '.join(filtered_text)[:200] + ('...' if len(' '.join(filtered_text)) > 200 else ''),
                                'note': 'Filtering done post-extraction (yt-dlp has no built-in time filtering)'
                            }
                            
                            print(f"    ✅ Success: {len(filtered_events)}/{len(events)} events in time range")
                            print(f"       Text length: {len(' '.join(filtered_text))} chars")
                        
                        else:
                            results[test_case['name']] = {
                                'success': False,
                                'error': 'No JSON subtitle file found'
                            }
                            print(f"    ❌ No JSON subtitle file found")
                        
            except Exception as e:
                results[test_case['name']] = {
                    'success': False,
                    'error': str(e),
                    'error_type': type(e).__name__
                }
                print(f"    ❌ Failed: {e}")
        
        self.results['filtering_tests'] = results
        return results
    
    def test_performance_comparison(self) -> Dict[str, Any]:
        """Compare yt-dlp vs youtube-transcript-api performance."""
        print("\n🏃 Performance Comparison: yt-dlp vs youtube-transcript-api")
        print("=" * 60)
        
        results = {}
        test_video_id = 'jNQXAC9IVRw'  # Short video for quick test
        
        # Test yt-dlp
        print(f"\nTesting yt-dlp with video: {test_video_id}")
        try:
            ydl_opts = {
                'skip_download': True,
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['en'],
                'subtitlesformat': 'vtt',
                'quiet': True,
                'no_warnings': True
            }
            
            start_time = time.time()
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f'https://www.youtube.com/watch?v={test_video_id}', download=False)
            yt_dlp_time = time.time() - start_time
            
            results['yt_dlp'] = {
                'success': True,
                'extraction_time': yt_dlp_time,
                'method': 'Full info extraction + subtitle availability'
            }
            print(f"  ✅ yt-dlp: {yt_dlp_time:.3f}s")
            
        except Exception as e:
            results['yt_dlp'] = {
                'success': False,
                'error': str(e),
                'extraction_time': None
            }
            print(f"  ❌ yt-dlp failed: {e}")
        
        # Test youtube-transcript-api
        print(f"\nTesting youtube-transcript-api with video: {test_video_id}")
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            
            start_time = time.time()
            transcript = YouTubeTranscriptApi.get_transcript(test_video_id)
            yt_api_time = time.time() - start_time
            
            results['youtube_transcript_api'] = {
                'success': True,
                'extraction_time': yt_api_time,
                'transcript_entries': len(transcript),
                'method': 'Direct transcript fetch'
            }
            print(f"  ✅ youtube-transcript-api: {yt_api_time:.3f}s ({len(transcript)} entries)")
            
        except Exception as e:
            results['youtube_transcript_api'] = {
                'success': False,
                'error': str(e),
                'extraction_time': None
            }
            print(f"  ❌ youtube-transcript-api failed: {e}")
        
        # Compare results
        if results.get('yt_dlp', {}).get('success') and results.get('youtube_transcript_api', {}).get('success'):
            yt_dlp_time = results['yt_dlp']['extraction_time']
            yt_api_time = results['youtube_transcript_api']['extraction_time']
            
            results['comparison'] = {
                'yt_dlp_faster': yt_dlp_time < yt_api_time,
                'time_difference': abs(yt_dlp_time - yt_api_time),
                'speed_ratio': max(yt_dlp_time, yt_api_time) / min(yt_dlp_time, yt_api_time)
            }
            
            faster = 'yt-dlp' if yt_dlp_time < yt_api_time else 'youtube-transcript-api'
            print(f"\n  📊 {faster} is {results['comparison']['speed_ratio']:.1f}x faster")
        
        self.results['performance_tests'] = results
        return results
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run the complete test suite."""
        print("🚀 Starting Comprehensive yt-dlp Transcript Testing")
        print("=" * 60)
        
        # Run tests in sequence
        self.test_basic_extraction()
        self.test_subtitle_formats()
        self.test_language_support()
        self.test_timestamp_filtering()
        self.test_performance_comparison()
        
        # Generate summary
        print("\n📊 TEST SUMMARY")
        print("=" * 60)
        
        # Basic extraction summary
        basic_success = sum(1 for r in self.results['basic_extraction'].values() if r.get('success'))
        basic_total = len(self.results['basic_extraction'])
        print(f"Basic extraction: {basic_success}/{basic_total} videos successful")
        
        # Format tests summary
        format_success = sum(1 for r in self.results['format_tests'].values() if r.get('success'))
        format_total = len(self.results['format_tests'])
        print(f"Format tests: {format_success}/{format_total} formats successful")
        
        # Language tests summary
        lang_tests = {k: v for k, v in self.results['language_tests'].items() if not k.startswith('_')}
        lang_success = sum(1 for r in lang_tests.values() if r.get('success'))
        lang_total = len(lang_tests)
        print(f"Language tests: {lang_success}/{lang_total} languages successful")
        
        # Overall assessment
        print(f"\n🎯 OVERALL ASSESSMENT:")
        if basic_success > 0:
            print("✅ yt-dlp can extract transcript metadata successfully")
            if format_success > 0:
                print("✅ Multiple subtitle formats supported")
            if lang_success > 0:
                print("✅ Multi-language support working")
        else:
            print("❌ Basic transcript extraction failing - check network/YouTube access")
        
        return self.results


def main():
    """Run the comprehensive test suite."""
    tester = YtDlpTranscriptTester()
    results = tester.run_all_tests()
    
    # Save results to file
    output_file = Path(__file__).parent / "ytdlp_test_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Full results saved to: {output_file}")
    print("\n🏁 Testing complete!")


if __name__ == "__main__":
    main()