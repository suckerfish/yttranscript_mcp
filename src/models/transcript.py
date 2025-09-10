"""Pydantic models for transcript data structures."""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
import re


class TranscriptRequest(BaseModel):
    """Request model for fetching YouTube transcripts."""
    
    video_id: str = Field(
        ..., 
        description="YouTube video ID (11 characters)",
        min_length=11,
        max_length=11
    )
    language_code: Optional[str] = Field(
        None,
        description="Language code (e.g., 'en', 'es', 'fr'). If not provided, will use auto-detected language."
    )
    preserve_formatting: bool = Field(
        True,
        description="Whether to preserve original timestamp formatting"
    )
    start_time: Optional[Union[int, float, str]] = Field(
        None,
        description="Start time in seconds to filter transcript"
    )
    end_time: Optional[Union[int, float, str]] = Field(
        None,
        description="End time in seconds to filter transcript"
    )
    
    @validator('video_id')
    def validate_video_id(cls, v: str) -> str:
        """Validate YouTube video ID format."""
        if not re.match(r'^[a-zA-Z0-9_-]{11}$', v):
            raise ValueError('Invalid YouTube video ID format')
        return v
    
    @validator('start_time', 'end_time', pre=True, allow_reuse=True)
    def validate_time_param(cls, v):
        """Parse and validate time parameters with robust type coercion for universal MCP client compatibility."""
        # Handle None and empty values
        if v is None:
            return None
        if v == "" or v == "null" or v == "undefined":
            return None
            
        # Handle numeric types
        if isinstance(v, (int, float)):
            if v < 0:
                raise ValueError("Time parameter must be non-negative")
            return float(v)
            
        # Handle string types with robust parsing
        if isinstance(v, str):
            # Strip whitespace and common formatting
            v_clean = v.strip()
            if not v_clean:
                return None
                
            try:
                # Handle common string representations
                if v_clean.lower() in ('null', 'none', 'undefined', 'nil'):
                    return None
                    
                # Parse numeric strings
                parsed = float(v_clean)
                if parsed < 0:
                    raise ValueError("Time parameter must be non-negative")
                return parsed
                
            except (ValueError, TypeError):
                raise ValueError(f"Time parameter must be a valid number, got: '{v}'")
                
        # Handle boolean (edge case)
        if isinstance(v, bool):
            raise ValueError("Time parameter cannot be a boolean")
            
        # Handle lists/objects (edge case)
        if isinstance(v, (list, dict)):
            raise ValueError(f"Time parameter must be a number, got {type(v).__name__}")
            
        # Fallback for unknown types
        raise ValueError(f"Invalid time parameter type: {type(v).__name__}")
    
    @validator('end_time', pre=False)
    def validate_time_range(cls, v: Optional[float], values: Dict) -> Optional[float]:
        """Validate that end_time is greater than start_time when both are provided."""
        # Both values should already be converted to float by the time parameter validator
        if v is not None and 'start_time' in values and values['start_time'] is not None:
            start_val = values['start_time']
            # Ensure both are floats (should already be converted by this point)
            if isinstance(start_val, (int, float)) and isinstance(v, (int, float)):
                if v < start_val:
                    raise ValueError('end_time must be greater than or equal to start_time')
        return v


class TranscriptEntry(BaseModel):
    """Individual transcript entry with timestamp."""
    
    text: str = Field(..., description="Transcript text")
    start: float = Field(..., description="Start time in seconds")
    duration: float = Field(..., description="Duration in seconds")


class LanguageInfo(BaseModel):
    """Information about available transcript languages."""
    
    language_code: str = Field(..., description="Language code")
    language_name: str = Field(..., description="Human-readable language name")
    is_generated: bool = Field(..., description="Whether transcript is auto-generated")
    is_translatable: bool = Field(..., description="Whether transcript can be translated")


class TranscriptResponse(BaseModel):
    """Response model for transcript data."""
    
    video_id: str = Field(..., description="YouTube video ID")
    language_code: str = Field(..., description="Language code used")
    language_name: str = Field(..., description="Human-readable language name")
    is_generated: bool = Field(..., description="Whether transcript is auto-generated")
    transcript: List[TranscriptEntry] = Field(..., description="List of transcript entries")
    plain_text: str = Field(..., description="Full transcript as plain text")
    total_duration: float = Field(..., description="Total video duration in seconds")
    word_count: int = Field(..., description="Total word count")


class SearchRequest(BaseModel):
    """Request model for searching within transcripts."""
    
    video_id: str = Field(
        ..., 
        description="YouTube video ID",
        min_length=11,
        max_length=11
    )
    query: str = Field(
        ..., 
        description="Search query text",
        min_length=1,
        max_length=1000
    )
    language_code: Optional[str] = Field(
        None,
        description="Language code for transcript to search"
    )
    case_sensitive: bool = Field(
        False,
        description="Whether search should be case sensitive"
    )
    context_window: int = Field(
        30,
        description="Seconds of context to include before/after matches",
        ge=0,
        le=300
    )
    
    @validator('video_id')
    def validate_video_id(cls, v: str) -> str:
        """Validate YouTube video ID format."""
        if not re.match(r'^[a-zA-Z0-9_-]{11}$', v):
            raise ValueError('Invalid YouTube video ID format')
        return v


class SearchResult(BaseModel):
    """Individual search result within transcript."""
    
    match_text: str = Field(..., description="Matched text")
    context_before: str = Field(..., description="Text before the match")
    context_after: str = Field(..., description="Text after the match")
    start_time: float = Field(..., description="Start time of match in seconds")
    end_time: float = Field(..., description="End time of match in seconds")
    timestamp_formatted: str = Field(..., description="Human-readable timestamp")


class SearchResponse(BaseModel):
    """Response model for transcript search results."""
    
    video_id: str = Field(..., description="YouTube video ID")
    query: str = Field(..., description="Search query used")
    language_code: str = Field(..., description="Language code of searched transcript")
    total_matches: int = Field(..., description="Total number of matches found")
    results: List[SearchResult] = Field(..., description="List of search results")