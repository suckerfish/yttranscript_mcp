"""YouTube transcript tools implementation using yt-dlp."""

import re
import json
import subprocess
import tempfile
import os
import asyncio
from typing import List, Optional, Dict, Any, Tuple, Union
from fastmcp.exceptions import ToolError

try:
    import yt_dlp
except ImportError:
    raise ImportError("yt-dlp is required. Install with: uv add yt-dlp")

# Handle both direct execution and module imports
try:
    from ..models.transcript import (
        TranscriptRequest,
        TranscriptResponse,
        TranscriptEntry,
        SearchRequest,
        SearchResponse,
        SearchResult,
        LanguageInfo,
    )
except ImportError:
    from models.transcript import (
        TranscriptRequest,
        TranscriptResponse,
        TranscriptEntry,
        SearchRequest,
        SearchResponse,
        SearchResult,
        LanguageInfo,
    )


def format_timestamp(seconds: float) -> str:
    """Format seconds into MM:SS or HH:MM:SS format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def extract_video_id(url_or_id: str) -> str:
    """Extract video ID from YouTube URL or return as-is if already an ID."""
    # If it's already an 11-character ID, return it
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
        return url_or_id
    
    # Extract from various YouTube URL formats
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com/watch\?.*?v=([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    
    raise ValueError(f"Could not extract video ID from: {url_or_id}")


def get_video_info(video_id: str) -> Dict[str, Any]:
    """Get video information including subtitle data using yt-dlp."""
    ydl_opts = {
        'skip_download': True,
        'quiet': True,
        'no_warnings': True
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f'https://www.youtube.com/watch?v={video_id}', download=False)
            return info
    except Exception as e:
        raise ToolError(f"Failed to get video info: {str(e)}")


def parse_vtt_content(content: str) -> List[TranscriptEntry]:
    """Parse VTT subtitle content into transcript entries."""
    entries = []
    lines = content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip VTT headers and notes
        if line.startswith('WEBVTT') or line.startswith('NOTE') or not line:
            i += 1
            continue
        
        # Check if this line contains a timestamp
        if '-->' in line:
            # Parse timestamp line
            time_parts = line.split(' --> ')
            if len(time_parts) == 2:
                start_time = parse_vtt_timestamp(time_parts[0].strip())
                end_time = parse_vtt_timestamp(time_parts[1].strip())
                duration = end_time - start_time
                
                # Get the text content (next non-empty lines)
                i += 1
                text_lines = []
                while i < len(lines) and lines[i].strip():
                    text_line = lines[i].strip()
                    # Remove VTT formatting tags
                    text_line = re.sub(r'<[^>]*>', '', text_line)
                    if text_line:
                        text_lines.append(text_line)
                    i += 1
                
                if text_lines:
                    text = ' '.join(text_lines)
                    entries.append(TranscriptEntry(
                        text=text,
                        start=start_time,
                        duration=duration
                    ))
        
        i += 1
    
    return entries


def parse_json3_content(content: str) -> List[TranscriptEntry]:
    """Parse JSON3 subtitle content into transcript entries."""
    try:
        data = json.loads(content)
        events = data.get('events', [])
        entries = []
        
        for event in events:
            start_time = event.get('tStartMs', 0) / 1000.0  # Convert ms to seconds
            duration_ms = event.get('dDurationMs', 0)
            duration = duration_ms / 1000.0 if duration_ms else 0
            
            # Extract text from segments
            segments = event.get('segs', [])
            text_parts = []
            for seg in segments:
                text = seg.get('utf8', '').strip()
                if text:
                    text_parts.append(text)
            
            if text_parts:
                text = ''.join(text_parts)
                entries.append(TranscriptEntry(
                    text=text,
                    start=start_time,
                    duration=duration
                ))
        
        return entries
    except json.JSONDecodeError as e:
        raise ToolError(f"Failed to parse JSON3 content: {str(e)}")


def parse_vtt_timestamp(timestamp: str) -> float:
    """Parse VTT timestamp format (HH:MM:SS.mmm) to seconds."""
    # Remove any extra formatting and extract only the timestamp part
    timestamp = timestamp.strip()
    
    # Remove alignment and positioning data (e.g., "align:start position:0%")
    # VTT timestamps can have additional formatting that needs to be stripped
    timestamp = re.sub(r'\s+(align|position|size|line|vertical):[^\s]*', '', timestamp)
    timestamp = timestamp.strip()
    
    # Handle different timestamp formats
    if '.' in timestamp:
        # Split on the first dot to handle decimals
        dot_parts = timestamp.split('.', 1)
        time_part = dot_parts[0]
        ms_part = dot_parts[1]
        
        # Remove any non-numeric characters from milliseconds part
        ms_part = re.sub(r'[^0-9]', '', ms_part)
        if ms_part:
            # Pad or truncate to 3 digits for milliseconds
            ms_part = ms_part[:3].ljust(3, '0')
            ms = float('0.' + ms_part)
        else:
            ms = 0
    else:
        time_part = timestamp
        ms = 0
    
    time_components = time_part.split(':')
    
    if len(time_components) == 3:
        hours, minutes, seconds = map(int, time_components)
        return hours * 3600 + minutes * 60 + seconds + ms
    elif len(time_components) == 2:
        minutes, seconds = map(int, time_components)
        return minutes * 60 + seconds + ms
    else:
        return float(time_part) + ms


def filter_transcript_by_time(entries: List[TranscriptEntry], start_time: Union[float, None] = None, end_time: Union[float, None] = None) -> List[TranscriptEntry]:
    """
    Filter transcript entries by time range.
    
    Args:
        entries: List of transcript entries
        start_time: Start time in seconds (inclusive)
        end_time: End time in seconds (inclusive)
    
    Returns:
        Filtered list of transcript entries
    """
    if start_time is None and end_time is None:
        return entries
    
    filtered_entries = []
    for entry in entries:
        entry_start = entry.start
        entry_end = entry.start + entry.duration
        
        # Check if entry overlaps with the time range
        if start_time is not None and entry_end < start_time:
            continue
        if end_time is not None and entry_start > end_time:
            continue
        
        filtered_entries.append(entry)
    
    return filtered_entries


async def fetch_subtitle_content_impl(video_id: str, language_code: Union[str, None] = None) -> Tuple[List[TranscriptEntry], str, str, bool]:
    """
    Fetch subtitle content using yt-dlp CLI and return parsed entries.
    This version uses subprocess calls to avoid YouTube's 429 rate limiting.
    
    Returns:
        Tuple of (entries, language_code, language_name, is_generated)
    """
    try:
        # Create temporary directory for subtitle downloads
        with tempfile.TemporaryDirectory() as temp_dir:
            # Prepare yt-dlp CLI command
            cmd = [
                'yt-dlp',
                '--write-auto-subs',
                '--skip-download',
                '--sub-format', 'vtt',
                '--quiet',
                '--no-warnings',
                '-o', os.path.join(temp_dir, '%(id)s.%(ext)s')
            ]
            
            # Add language specification if provided
            if language_code:
                cmd.extend(['--sub-langs', language_code])
            
            # Add video URL
            video_url = f'https://www.youtube.com/watch?v={video_id}'
            cmd.append(video_url)
            
            # Execute yt-dlp CLI
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=temp_dir
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
            
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8') if stderr else 'Unknown error'
                if 'HTTP Error 429' in error_msg:
                    raise ToolError("Rate limited by YouTube. Please try again later.")
                elif 'No subtitles' in error_msg or 'Unable to download' in error_msg:
                    raise ToolError(f"No subtitles available for video {video_id}")
                else:
                    raise ToolError(f"Failed to download subtitles: {error_msg}")
            
            # Find downloaded subtitle files
            subtitle_files = [f for f in os.listdir(temp_dir) if f.endswith('.vtt')]
            
            if not subtitle_files:
                raise ToolError(f"No subtitle files downloaded for video {video_id}")
            
            # Use the first available subtitle file
            subtitle_file = subtitle_files[0]
            subtitle_path = os.path.join(temp_dir, subtitle_file)
            
            # Extract language info from filename
            # Format: videoId.languageCode.vtt
            parts = subtitle_file.split('.')
            if len(parts) >= 3:
                detected_lang = parts[1]
                language_name = detected_lang.upper()
                is_generated = True  # CLI auto-subs are always generated
            else:
                detected_lang = language_code or 'unknown'
                language_name = detected_lang.upper()
                is_generated = True
            
            # Read and parse subtitle content
            with open(subtitle_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse VTT content (reuse existing parser)
            entries = parse_vtt_content(content)
            
            return entries, detected_lang, language_name, is_generated
            
    except asyncio.TimeoutError:
        raise ToolError("Subtitle download timed out")
    except Exception as e:
        if isinstance(e, ToolError):
            raise
        raise ToolError(f"Failed to fetch subtitles via CLI: {str(e)}")


async def fetch_subtitle_content(video_id: str, language_code: Union[str, None] = None) -> Tuple[List[TranscriptEntry], str, str, bool]:
    """
    Fetch subtitle content using yt-dlp CLI and return parsed entries.
    This replaces the hybrid approach to avoid YouTube's rate limiting on direct HTTP requests.
    
    Returns:
        Tuple of (entries, language_code, language_name, is_generated)
    """
    return await fetch_subtitle_content_impl(video_id, language_code)



async def get_transcript_internal(
    video_id: str,
    language_code: Union[str, None] = None,
    preserve_formatting: bool = True,
    start_time: Union[float, None] = None,
    end_time: Union[float, None] = None
) -> TranscriptResponse:
    """Internal function to get transcript data."""
    try:
        # Extract video ID if URL was provided
        clean_video_id = extract_video_id(video_id)
        
        # Validate request
        request = TranscriptRequest(
            video_id=clean_video_id,
            language_code=language_code,
            preserve_formatting=preserve_formatting,
            start_time=start_time,
            end_time=end_time
        )
        
        # Fetch subtitle content using yt-dlp CLI
        entries, selected_lang, language_name, is_generated = await fetch_subtitle_content(
            request.video_id, request.language_code
        )
        
        if not entries:
            raise ToolError("No transcript content found")
        
        # Apply time filtering if specified (use the validated values from the request model)
        if request.start_time is not None or request.end_time is not None:
            entries = filter_transcript_by_time(entries, request.start_time, request.end_time)
        
        # Calculate total duration and word count
        total_duration = max(entry.start + entry.duration for entry in entries) if entries else 0
        
        # Create plain text version
        if preserve_formatting:
            plain_text_lines = []
            for entry in entries:
                timestamp = format_timestamp(entry.start)
                plain_text_lines.append(f"[{timestamp}] {entry.text}")
            plain_text = "\n".join(plain_text_lines)
        else:
            plain_text = " ".join(entry.text for entry in entries)
        
        word_count = len(plain_text.split())
        
        return TranscriptResponse(
            video_id=request.video_id,
            language_code=selected_lang,
            language_name=language_name,
            is_generated=is_generated,
            transcript=entries,
            plain_text=plain_text,
            total_duration=total_duration,
            word_count=word_count
        )
        
    except ToolError:
        raise
    except Exception as e:
        raise ToolError(f"Failed to fetch transcript: {str(e)}")


def register_transcript_tools(mcp):
    """Register all transcript-related tools with the MCP server."""
    
    @mcp.tool()
    async def get_transcript(
        video_id: str,
        language_code: Union[str, None] = None,
        preserve_formatting: bool = True,
        start_time: Union[int, float, str, None] = None,
        end_time: Union[int, float, str, None] = None
    ) -> TranscriptResponse:
        """
        Fetch the transcript for a YouTube video using yt-dlp.
        
        Args:
            video_id: YouTube video ID or URL
            language_code: Optional language code (e.g., 'en', 'es'). If not provided, uses auto-detected language.
            preserve_formatting: Whether to preserve timestamp formatting in plain text
            start_time: Optional start time in seconds to filter transcript
            end_time: Optional end time in seconds to filter transcript
            
        Returns:
            Complete transcript data with metadata
        """
        return await get_transcript_internal(video_id, language_code, preserve_formatting, start_time, end_time)
    
    @mcp.tool()
    async def search_transcript(
        video_id: str,
        query: str,
        language_code: Union[str, None] = None,
        case_sensitive: bool = False,
        context_window: int = 30
    ) -> SearchResponse:
        """
        Search for specific text within a YouTube video transcript.
        
        Args:
            video_id: YouTube video ID or URL
            query: Text to search for
            language_code: Optional language code for transcript
            case_sensitive: Whether search should be case sensitive
            context_window: Seconds of context to include before/after matches
            
        Returns:
            Search results with context and timestamps
        """
        try:
            # Extract video ID if URL was provided
            clean_video_id = extract_video_id(video_id)
            
            # Validate request
            request = SearchRequest(
                video_id=clean_video_id,
                query=query,
                language_code=language_code,
                case_sensitive=case_sensitive,
                context_window=context_window
            )
            
            # First get the transcript
            transcript_response = await get_transcript_internal(
                video_id=request.video_id,
                language_code=request.language_code,
                preserve_formatting=False
            )
            
            # Perform search
            search_flags = 0 if case_sensitive else re.IGNORECASE
            pattern = re.compile(re.escape(query), search_flags)
            
            results = []
            entries = transcript_response.transcript
            
            for i, entry in enumerate(entries):
                matches = list(pattern.finditer(entry.text))
                
                for match in matches:
                    # Find context entries
                    context_start_time = max(0, entry.start - context_window)
                    context_end_time = entry.start + entry.duration + context_window
                    
                    # Collect context text
                    context_before_parts = []
                    context_after_parts = []
                    
                    # Before context
                    for j in range(i - 1, -1, -1):
                        if entries[j].start + entries[j].duration >= context_start_time:
                            context_before_parts.insert(0, entries[j].text)
                        else:
                            break
                    
                    # After context
                    for j in range(i + 1, len(entries)):
                        if entries[j].start <= context_end_time:
                            context_after_parts.append(entries[j].text)
                        else:
                            break
                    
                    result = SearchResult(
                        match_text=match.group(),
                        context_before=" ".join(context_before_parts),
                        context_after=" ".join(context_after_parts),
                        start_time=entry.start,
                        end_time=entry.start + entry.duration,
                        timestamp_formatted=format_timestamp(entry.start)
                    )
                    results.append(result)
            
            return SearchResponse(
                video_id=request.video_id,
                query=request.query,
                language_code=transcript_response.language_code,
                total_matches=len(results),
                results=results
            )
            
        except Exception as e:
            raise ToolError(f"Failed to search transcript: {str(e)}")
    
    @mcp.tool()
    async def get_available_languages(video_id: str) -> List[LanguageInfo]:
        """
        Get list of available transcript languages for a YouTube video using yt-dlp.
        
        Args:
            video_id: YouTube video ID or URL
            
        Returns:
            List of available languages with metadata
        """
        try:
            # Extract video ID if URL was provided
            clean_video_id = extract_video_id(video_id)
            
            # Validate video ID
            if not re.match(r'^[a-zA-Z0-9_-]{11}$', clean_video_id):
                raise ToolError("Invalid YouTube video ID format")
            
            # Get video info using yt-dlp
            info = get_video_info(clean_video_id)
            
            manual_subs = info.get('subtitles', {})
            auto_subs = info.get('automatic_captions', {})
            
            languages = []
            
            # Add manual subtitles
            for lang_code in manual_subs.keys():
                lang_info = LanguageInfo(
                    language_code=lang_code,
                    language_name=lang_code.upper(),  # yt-dlp doesn't provide full language names
                    is_generated=False,
                    is_translatable=True  # Assume manual subtitles can be translated
                )
                languages.append(lang_info)
            
            # Add auto-generated captions
            for lang_code in auto_subs.keys():
                # Skip if we already have a manual version of this language
                if lang_code not in manual_subs:
                    lang_info = LanguageInfo(
                        language_code=lang_code,
                        language_name=lang_code.upper(),
                        is_generated=True,
                        is_translatable=True
                    )
                    languages.append(lang_info)
            
            return languages
            
        except ToolError:
            raise
        except Exception as e:
            raise ToolError(f"Failed to get available languages: {str(e)}")
    
    @mcp.tool()
    async def get_transcript_summary(
        video_id: str,
        language_code: Union[str, None] = None,
        max_length: int = 500
    ) -> Dict[str, Any]:
        """
        Get a summary of the transcript including key statistics and sample text.
        
        Args:
            video_id: YouTube video ID or URL
            language_code: Optional language code
            max_length: Maximum length of sample text
            
        Returns:
            Summary with statistics and sample text
        """
        try:
            # Get the full transcript
            transcript_response = await get_transcript_internal(
                video_id=video_id,
                language_code=language_code,
                preserve_formatting=False
            )
            
            # Calculate basic statistics
            total_words = transcript_response.word_count
            total_entries = len(transcript_response.transcript)
            avg_words_per_entry = total_words / total_entries if total_entries > 0 else 0
            
            # Calculate advanced analytics
            words_per_minute = (total_words / (transcript_response.total_duration / 60)) if transcript_response.total_duration > 0 else 0
            
            # Analyze content patterns
            text_lower = transcript_response.plain_text.lower()
            
            # Common filler words detection
            filler_words = ['um', 'uh', 'like', 'you know', 'i mean', 'basically', 'actually', 'literally', 'sort of', 'kind of']
            filler_count = sum(text_lower.count(filler) for filler in filler_words)
            filler_percentage = (filler_count / total_words * 100) if total_words > 0 else 0
            
            # Question detection
            question_count = transcript_response.plain_text.count('?')
            
            # Exclamation detection for enthusiasm
            exclamation_count = transcript_response.plain_text.count('!')
            
            # Most frequent words (excluding common stop words)
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their', 'this', 'that', 'these', 'those'}
            words = [word.strip('.,!?;:"()[]{}') for word in text_lower.split()]
            word_freq = {}
            for word in words:
                if len(word) > 2 and word not in stop_words and word.isalpha():
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Top 5 most frequent meaningful words
            top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Content segments analysis
            entries = transcript_response.transcript
            segment_lengths = [len(entry.text.split()) for entry in entries]
            avg_segment_length = sum(segment_lengths) / len(segment_lengths) if segment_lengths else 0
            max_segment_length = max(segment_lengths) if segment_lengths else 0
            min_segment_length = min(segment_lengths) if segment_lengths else 0
            
            # Speaking pace analysis
            if transcript_response.total_duration > 0:
                if words_per_minute < 120:
                    pace_description = "slow"
                elif words_per_minute < 160:
                    pace_description = "normal"
                elif words_per_minute < 200:
                    pace_description = "fast"
                else:
                    pace_description = "very fast"
            else:
                pace_description = "unknown"
            
            # Enhanced sample text with key moments
            sample_sections = []
            
            # Beginning sample
            beginning_text = transcript_response.plain_text[:max_length//3]
            if len(transcript_response.plain_text) > max_length//3:
                beginning_text = beginning_text.rsplit(' ', 1)[0] + "..."
            sample_sections.append(f"[Beginning] {beginning_text}")
            
            # Middle sample (if transcript is long enough)
            if transcript_response.total_duration > 60:
                middle_start = len(transcript_response.plain_text) // 2 - max_length//6
                middle_end = len(transcript_response.plain_text) // 2 + max_length//6
                middle_text = transcript_response.plain_text[middle_start:middle_end]
                if middle_start > 0:
                    middle_text = "..." + middle_text
                if middle_end < len(transcript_response.plain_text):
                    middle_text = middle_text.rsplit(' ', 1)[0] + "..."
                sample_sections.append(f"[Middle] {middle_text}")
            
            # End sample (if different from beginning)
            if transcript_response.total_duration > 30:
                end_text = transcript_response.plain_text[-max_length//3:]
                if len(transcript_response.plain_text) > max_length//3:
                    end_text = "..." + end_text.split(' ', 1)[1] if ' ' in end_text else end_text
                sample_sections.append(f"[End] {end_text}")
            
            enhanced_sample = "\n\n".join(sample_sections)
            
            return {
                "video_id": transcript_response.video_id,
                "language_code": transcript_response.language_code,
                "language_name": transcript_response.language_name,
                "is_generated": transcript_response.is_generated,
                "statistics": {
                    "duration": {
                        "total_seconds": transcript_response.total_duration,
                        "formatted": format_timestamp(transcript_response.total_duration)
                    },
                    "content": {
                        "total_words": total_words,
                        "total_segments": total_entries,
                        "average_words_per_segment": round(avg_words_per_entry, 1),
                        "words_per_minute": round(words_per_minute, 1),
                        "speaking_pace": pace_description
                    },
                    "engagement": {
                        "questions_asked": question_count,
                        "exclamations": exclamation_count,
                        "filler_words_detected": filler_count,
                        "filler_percentage": round(filler_percentage, 1)
                    },
                    "segments": {
                        "average_length_words": round(avg_segment_length, 1),
                        "longest_segment_words": max_segment_length,
                        "shortest_segment_words": min_segment_length
                    },
                    "reading_time": {
                        "estimated_minutes_slow": round(total_words / 150, 1),
                        "estimated_minutes_normal": round(total_words / 200, 1),
                        "estimated_minutes_fast": round(total_words / 250, 1)
                    }
                },
                "content_analysis": {
                    "top_words": [{"word": word, "frequency": freq} for word, freq in top_words],
                    "content_indicators": {
                        "has_questions": question_count > 0,
                        "high_energy": exclamation_count > total_words * 0.01,  # More than 1% exclamations
                        "conversational": filler_percentage > 2.0,  # More than 2% filler words
                        "formal_speech": filler_percentage < 0.5   # Less than 0.5% filler words
                    }
                },
                "sample_content": enhanced_sample
            }
            
        except Exception as e:
            raise ToolError(f"Failed to get transcript summary: {str(e)}")