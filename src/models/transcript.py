"""Pydantic models for transcript data structures."""

from typing import List, Optional, Dict, Any
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
    
    @validator('video_id')
    def validate_video_id(cls, v: str) -> str:
        """Validate YouTube video ID format."""
        if not re.match(r'^[a-zA-Z0-9_-]{11}$', v):
            raise ValueError('Invalid YouTube video ID format')
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