"""YouTube transcript tools implementation using yt-dlp."""

import re
import json
import requests
from typing import List, Optional, Dict, Any, Tuple
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
    # Remove any extra formatting
    timestamp = timestamp.strip()
    
    # Handle different timestamp formats
    if '.' in timestamp:
        time_part, ms_part = timestamp.split('.')
        ms = float('0.' + ms_part)
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


def filter_transcript_by_time(entries: List[TranscriptEntry], start_time: Optional[float] = None, end_time: Optional[float] = None) -> List[TranscriptEntry]:
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


def fetch_subtitle_content(video_id: str, language_code: Optional[str] = None) -> Tuple[List[TranscriptEntry], str, str, bool]:
    """
    Fetch subtitle content using yt-dlp and return parsed entries.
    
    Returns:
        Tuple of (entries, language_code, language_name, is_generated)
    """
    info = get_video_info(video_id)
    
    manual_subs = info.get('subtitles', {})
    auto_subs = info.get('automatic_captions', {})
    
    # Determine which subtitles to use
    subtitle_data = None
    selected_lang = None
    is_generated = False
    language_name = None
    
    if language_code:
        # Try specific language
        if language_code in manual_subs:
            subtitle_data = manual_subs[language_code]
            selected_lang = language_code
            is_generated = False
        elif language_code in auto_subs:
            subtitle_data = auto_subs[language_code]
            selected_lang = language_code
            is_generated = True
        else:
            raise ToolError(f"No subtitles found for language: {language_code}")
    else:
        # Auto-select best available
        if 'en' in manual_subs:
            subtitle_data = manual_subs['en']
            selected_lang = 'en'
            is_generated = False
        elif 'en' in auto_subs:
            subtitle_data = auto_subs['en']
            selected_lang = 'en'
            is_generated = True
        else:
            # Fall back to any available subtitle
            if manual_subs:
                selected_lang = list(manual_subs.keys())[0]
                subtitle_data = manual_subs[selected_lang]
                is_generated = False
            elif auto_subs:
                selected_lang = list(auto_subs.keys())[0]
                subtitle_data = auto_subs[selected_lang]
                is_generated = True
            else:
                raise ToolError("No subtitles available for this video")
    
    # Set language name
    language_name = selected_lang.upper() if selected_lang else "Unknown"
    
    # Find best format (prefer VTT, then JSON3)
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
    
    if not subtitle_url and subtitle_data:
        # Fallback to first available
        subtitle_url = subtitle_data[0].get('url')
        subtitle_format = subtitle_data[0].get('ext', 'unknown')
    
    if not subtitle_url:
        raise ToolError("No subtitle URL found")
    
    # Fetch content
    try:
        response = requests.get(subtitle_url, timeout=10)
        response.raise_for_status()
        content = response.text
    except requests.RequestException as e:
        raise ToolError(f"Failed to fetch subtitle content: {str(e)}")
    
    # Parse content based on format
    if subtitle_format == 'vtt':
        entries = parse_vtt_content(content)
    elif subtitle_format == 'json3':
        entries = parse_json3_content(content)
    else:
        raise ToolError(f"Unsupported subtitle format: {subtitle_format}")
    
    return entries, selected_lang, language_name, is_generated


async def get_transcript_internal(
    video_id: str,
    language_code: Optional[str] = None,
    preserve_formatting: bool = True,
    start_time: Optional[float] = None,
    end_time: Optional[float] = None
) -> TranscriptResponse:
    """Internal function to get transcript data."""
    try:
        # Extract video ID if URL was provided
        clean_video_id = extract_video_id(video_id)
        
        # Validate request
        request = TranscriptRequest(
            video_id=clean_video_id,
            language_code=language_code,
            preserve_formatting=preserve_formatting
        )
        
        # Fetch subtitle content using yt-dlp
        entries, selected_lang, language_name, is_generated = fetch_subtitle_content(
            request.video_id, request.language_code
        )
        
        if not entries:
            raise ToolError("No transcript content found")
        
        # Apply time filtering if specified
        if start_time is not None or end_time is not None:
            entries = filter_transcript_by_time(entries, start_time, end_time)
        
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
        language_code: Optional[str] = None,
        preserve_formatting: bool = True,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
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
        language_code: Optional[str] = None,
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
        language_code: Optional[str] = None,
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
            
            # Calculate additional statistics
            total_words = transcript_response.word_count
            total_entries = len(transcript_response.transcript)
            avg_words_per_entry = total_words / total_entries if total_entries > 0 else 0
            
            # Get sample text (first portion)
            sample_text = transcript_response.plain_text[:max_length]
            if len(transcript_response.plain_text) > max_length:
                sample_text += "..."
            
            return {
                "video_id": transcript_response.video_id,
                "language_code": transcript_response.language_code,
                "language_name": transcript_response.language_name,
                "is_generated": transcript_response.is_generated,
                "statistics": {
                    "total_duration_seconds": transcript_response.total_duration,
                    "total_duration_formatted": format_timestamp(transcript_response.total_duration),
                    "total_words": total_words,
                    "total_entries": total_entries,
                    "average_words_per_entry": round(avg_words_per_entry, 2),
                    "estimated_reading_time_minutes": round(total_words / 200, 1)  # Assuming 200 WPM
                },
                "sample_text": sample_text
            }
            
        except Exception as e:
            raise ToolError(f"Failed to get transcript summary: {str(e)}")