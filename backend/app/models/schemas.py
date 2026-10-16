from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class BitrateEnum(str, Enum):
    B_128K = "128k"
    B_192K = "192k"
    B_256K = "256k"
    B_320K = "320k"


class JobStatusEnum(str, Enum):
    VALIDATING = "validating"
    DOWNLOADING = "downloading"
    CONVERTING = "converting"
    COMPLETED = "completed"
    FAILED = "failed"


class ConvertRequest(BaseModel):
    url: str = Field(
        ...,
        description="Public media URL from Instagram, YouTube, or Facebook",
        examples=["https://www.instagram.com/reel/Daf2gF3vCzS/", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"]
    )
    platform: Optional[str] = Field(
        default="auto",
        description="Target platform: instagram, youtube, facebook, or auto",
        examples=["instagram", "youtube", "facebook", "auto"]
    )
    bitrate: Optional[str] = Field(
        default="192k",
        description="Audio bitrate. Supported values: 128k, 192k, 256k, 320k",
        examples=["192k"]
    )

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v: Optional[str]) -> str:
        if v is None:
            return "auto"
        normalized = v.strip().lower()
        if normalized not in {"auto", "instagram", "youtube", "facebook"}:
            return "auto"
        return normalized

    @field_validator("bitrate")
    @classmethod
    def validate_bitrate(cls, v: Optional[str]) -> str:
        if v is None:
            return "192k"
        normalized = v.strip().lower()
        valid = {"128k", "192k", "256k", "320k"}
        if normalized not in valid:
            raise ValueError(f"Invalid bitrate '{v}'. Supported bitrates are: 128k, 192k, 256k, 320k")
        return normalized


class ConvertResponse(BaseModel):
    job_id: str = Field(..., description="Unique UUID for tracking the conversion job")
    status: str = Field(default="processing", description="Initial job status")


class AudioMetadata(BaseModel):
    filename: str = Field(default="audio.mp3", description="Audio filename")
    title: Optional[str] = Field(None, description="Media title")
    platform: Optional[str] = Field(None, description="Source platform")
    duration: Optional[str] = Field(None, description="Formatted duration (MM:SS)")
    duration_seconds: Optional[float] = Field(None, description="Duration in seconds")
    bitrate: Optional[str] = Field(None, description="Audio bitrate")
    file_size: Optional[str] = Field(None, description="Human-readable file size")
    file_size_bytes: Optional[int] = Field(None, description="File size in bytes")


class VideoMetadata(BaseModel):
    filename: str = Field(default="video.mp4", description="Video filename")
    title: Optional[str] = Field(None, description="Media title")
    platform: Optional[str] = Field(None, description="Source platform")
    file_size: Optional[str] = Field(None, description="Human-readable file size")
    file_size_bytes: Optional[int] = Field(None, description="File size in bytes")


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatusEnum
    platform: Optional[str] = Field(None, description="Platform source: instagram, youtube, facebook")
    progress: int = Field(default=0, ge=0, le=100, description="Progress percentage")
    current_step: Optional[str] = Field(None, description="Current descriptive step")
    download_url: Optional[str] = Field(None, description="Relative URL to download the converted MP3 file")
    video_download_url: Optional[str] = Field(None, description="Relative URL to download the original MP4 video")
    fullscreen_download_url: Optional[str] = Field(None, description="Relative URL to download the cropped 16:9 full-screen MP4 video if letterboxed")
    metadata: Optional[AudioMetadata] = Field(None, description="Audio file metadata upon completion")
    video_metadata: Optional[VideoMetadata] = Field(None, description="Video file metadata upon completion")
    fullscreen_metadata: Optional[VideoMetadata] = Field(None, description="Cropped full-screen video metadata if applicable")
    error: Optional[str] = Field(None, description="Error message if conversion failed")


class ErrorResponse(BaseModel):
    success: bool = False
    error: str = Field(..., description="Descriptive error message")
