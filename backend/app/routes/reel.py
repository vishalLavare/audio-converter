import asyncio
import logging
import uuid
from typing import Dict, Optional
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Response, status
from fastapi.responses import FileResponse, JSONResponse

from app.config import settings
from app.models.schemas import (
    AudioMetadata,
    VideoMetadata,
    ConvertRequest,
    ConvertResponse,
    JobStatusEnum,
    JobStatusResponse,
    ErrorResponse
)
from app.services.cleanup_service import cleanup_service
from app.services.ffmpeg_service import ffmpeg_service, NoAudioStreamError, ConversionTimeoutError, FFmpegError
from app.services.media_service import media_service, MediaRetrievalError
from app.utils.validators import (
    validate_and_normalize_reel_url,
    validate_and_normalize_url,
    validate_job_id,
    ValidationError
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reel", tags=["Media Converter"])

# In-memory store for active conversion jobs
# Structure: job_id -> dict of status, progress, current_step, error, metadata, created_at
jobs_db: Dict[str, dict] = {}


async def process_conversion_task(job_id: str, normalized_url: str, bitrate: str, platform: str = "instagram"):
    """
    Background worker that runs the conversion pipeline:
    1. Validating URL (15%)
    2. Getting public media & Downloading video (35% -> 50%)
    3. Extracting audio (75%)
    4. Converting to MP3 (90%)
    5. Completed (100%)
    """
    job_dir = cleanup_service.create_job_dir(job_id)
    output_mp3 = job_dir / "output.mp3"
    platform_name = platform.capitalize() if platform else "Media"

    try:
        # Step 1: Validating
        jobs_db[job_id]["status"] = JobStatusEnum.VALIDATING
        jobs_db[job_id]["progress"] = 15
        jobs_db[job_id]["current_step"] = f"Validating public {platform_name} URL..."
        await asyncio.sleep(0.4)

        # Step 2 & 3: Getting public media & Downloading
        jobs_db[job_id]["status"] = JobStatusEnum.DOWNLOADING
        jobs_db[job_id]["progress"] = 35
        jobs_db[job_id]["current_step"] = f"Connecting to {platform_name}..."
        await asyncio.sleep(0.4)

        jobs_db[job_id]["progress"] = 50
        jobs_db[job_id]["current_step"] = f"Downloading {platform_name} video stream..."

        # Compliantly retrieve public media
        video_path, info_dict = await media_service.retrieve_public_media(normalized_url, job_dir, platform=platform)

        # Standardize video file as video.mp4 in job_dir
        canonical_video = job_dir / "video.mp4"
        if video_path != canonical_video and video_path.exists():
            try:
                if canonical_video.exists():
                    canonical_video.unlink()
                video_path.rename(canonical_video)
                video_path = canonical_video
            except Exception:
                pass

        # Calculate sanitized title for clean file downloads
        raw_title = info_dict.get("title") if info_dict else None
        clean_title = None
        if raw_title:
            clean_title = "".join(c for c in raw_title if c.isalnum() or c in (" ", "-", "_")).strip()
            clean_title = clean_title[:50].strip()

        if platform == "instagram":
            audio_filename = "instagram_reel_audio.mp3"
            video_filename = "instagram_reel.mp4"
        elif platform == "youtube":
            audio_filename = f"{clean_title}.mp3" if clean_title else "youtube_audio.mp3"
            video_filename = f"{clean_title}.mp4" if clean_title else "youtube_video.mp4"
        elif platform == "facebook":
            audio_filename = f"{clean_title}.mp3" if clean_title else "facebook_audio.mp3"
            video_filename = f"{clean_title}.mp4" if clean_title else "facebook_video.mp4"
        else:
            audio_filename = f"{clean_title}.mp3" if clean_title else "media_audio.mp3"
            video_filename = f"{clean_title}.mp4" if clean_title else "media_video.mp4"

        # Step 4 & 5: Extracting audio & Converting to MP3
        jobs_db[job_id]["status"] = JobStatusEnum.CONVERTING
        jobs_db[job_id]["progress"] = 75
        jobs_db[job_id]["current_step"] = "Extracting audio stream..."
        await asyncio.sleep(0.4)

        jobs_db[job_id]["progress"] = 90
        jobs_db[job_id]["current_step"] = f"Converting audio to MP3 ({bitrate})..."

        # Run FFmpeg conversion in threadpool
        metadata = await asyncio.to_thread(
            ffmpeg_service.extract_audio,
            video_path,
            output_mp3,
            bitrate,
            audio_filename,
            raw_title,
            platform
        )

        # Retain video file for user video download and gather video metadata
        video_size_bytes = video_path.stat().st_size if video_path.exists() else 0
        video_metadata = {
            "filename": video_filename,
            "title": raw_title,
            "platform": platform,
            "file_size": ffmpeg_service._format_size(video_size_bytes),
            "file_size_bytes": video_size_bytes
        }

        # Check for letterboxing and generate full-screen (16:9) video if applicable
        fullscreen_video = job_dir / "video_fullscreen.mp4"
        fs_filename = f"{clean_title} (Full Screen).mp4" if clean_title else f"{platform}_video_fullscreen.mp4"
        fullscreen_meta = await asyncio.to_thread(
            ffmpeg_service.detect_and_crop_black_bars,
            video_path,
            fullscreen_video,
            fs_filename,
            raw_title,
            platform
        )

        # Step 6: Completed
        jobs_db[job_id]["status"] = JobStatusEnum.COMPLETED
        jobs_db[job_id]["progress"] = 100
        jobs_db[job_id]["current_step"] = f"{platform_name} media processed successfully."
        jobs_db[job_id]["download_url"] = f"/api/reel/download/{job_id}"
        jobs_db[job_id]["video_download_url"] = f"/api/reel/download-video/{job_id}"
        if fullscreen_meta:
            jobs_db[job_id]["fullscreen_download_url"] = f"/api/reel/download-video-fullscreen/{job_id}"
            jobs_db[job_id]["fullscreen_metadata"] = fullscreen_meta
        else:
            jobs_db[job_id]["fullscreen_download_url"] = None
            jobs_db[job_id]["fullscreen_metadata"] = None
        jobs_db[job_id]["metadata"] = metadata
        jobs_db[job_id]["video_metadata"] = video_metadata
        jobs_db[job_id]["error"] = None
        logger.info(f"Job {job_id} ({platform}) completed successfully.")

    except MediaRetrievalError as me:
        logger.warning(f"Media retrieval error for job {job_id}: {me.message}")
        jobs_db[job_id]["status"] = JobStatusEnum.FAILED
        jobs_db[job_id]["error"] = me.message
        if "photo" in me.message.lower() or "image" in me.message.lower():
            jobs_db[job_id]["current_step"] = "Post contains only photos/images (no video or audio stream)."
        else:
            jobs_db[job_id]["current_step"] = f"Failed to retrieve public {platform_name} media."
    except NoAudioStreamError as ne:
        logger.warning(f"No audio stream for job {job_id}: {ne}")
        jobs_db[job_id]["status"] = JobStatusEnum.FAILED
        jobs_db[job_id]["error"] = f"This {platform_name} video does not contain an audio stream."
        jobs_db[job_id]["current_step"] = "No audio stream detected."
    except ConversionTimeoutError as te:
        logger.error(f"Conversion timeout for job {job_id}: {te}")
        jobs_db[job_id]["status"] = JobStatusEnum.FAILED
        jobs_db[job_id]["error"] = "Processing timed out. Please try again."
        jobs_db[job_id]["current_step"] = "Processing timed out."
    except FFmpegError as fe:
        logger.error(f"FFmpeg error for job {job_id}: {fe}")
        jobs_db[job_id]["status"] = JobStatusEnum.FAILED
        jobs_db[job_id]["error"] = "Audio conversion failed. Please try again."
        jobs_db[job_id]["current_step"] = "Audio conversion failed."
    except Exception as ex:
        logger.error(f"Unexpected error processing job {job_id}: {ex}", exc_info=True)
        jobs_db[job_id]["status"] = JobStatusEnum.FAILED
        jobs_db[job_id]["error"] = "An unexpected error occurred during processing."
        jobs_db[job_id]["current_step"] = "Processing failed."


@router.post(
    "/convert",
    response_model=ConvertResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Validation or bad request error"},
        429: {"description": "Too many requests"}
    },
    summary="Submit a video/audio URL for conversion",
    description="Validates a public Instagram, YouTube, or Facebook URL, extracts audio, and converts to MP3."
)
async def convert_reel(
    payload: ConvertRequest,
    background_tasks: BackgroundTasks
):
    # Validate and normalize URL across supported platforms
    try:
        platform_choice = payload.platform or "auto"
        normalized_url, media_id, detected_platform = validate_and_normalize_url(
            payload.url,
            platform_choice
        )
    except ValidationError as ve:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"success": False, "error": ve.message}
        )

    bitrate = payload.bitrate or settings.DEFAULT_BITRATE
    job_id = str(uuid.uuid4())

    # Initialize job in store
    jobs_db[job_id] = {
        "job_id": job_id,
        "platform": detected_platform,
        "status": JobStatusEnum.VALIDATING,
        "progress": 5,
        "current_step": f"Initializing {detected_platform.capitalize()} conversion job...",
        "download_url": None,
        "video_download_url": None,
        "metadata": None,
        "video_metadata": None,
        "error": None,
        "url": normalized_url,
        "bitrate": bitrate
    }

    # Queue background processing
    background_tasks.add_task(process_conversion_task, job_id, normalized_url, bitrate, detected_platform)

    return ConvertResponse(job_id=job_id, status="processing")


@router.get(
    "/status/{job_id}",
    response_model=JobStatusResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid Job ID"},
        404: {"model": ErrorResponse, "description": "Job not found"}
    },
    summary="Get status of conversion job",
    description="Poll this endpoint to retrieve conversion progress, status, metadata, and download link."
)
async def get_job_status(job_id: str):
    # Validate Job ID format to protect against path traversal
    try:
        valid_id = validate_job_id(job_id)
    except ValidationError:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"success": False, "error": "Invalid job ID."}
        )

    job = jobs_db.get(valid_id)
    if not job:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"success": False, "error": "Conversion job not found or expired."}
        )

    meta_obj = AudioMetadata(**job["metadata"]) if job.get("metadata") else None
    video_meta_obj = VideoMetadata(**job["video_metadata"]) if job.get("video_metadata") else None

    return JobStatusResponse(
        job_id=valid_id,
        status=job["status"],
        platform=job.get("platform", "instagram"),
        progress=job.get("progress", 0),
        current_step=job.get("current_step"),
        download_url=job.get("download_url"),
        video_download_url=job.get("video_download_url"),
        metadata=meta_obj,
        video_metadata=video_meta_obj,
        error=job.get("error")
    )


@router.get(
    "/download-video/{job_id}",
    summary="Download original Reel MP4 video",
    description="Returns the downloaded Instagram Reel MP4 video as an attachment."
)
async def download_video(job_id: str):
    # Validate Job ID format
    try:
        valid_id = validate_job_id(job_id)
    except ValidationError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job ID.")

    job_dir = cleanup_service.get_job_dir(valid_id)
    video_file = job_dir / "video.mp4"
    if not video_file.exists():
        candidates = list(job_dir.glob("input.*"))
        if candidates:
            video_file = candidates[0]

    if not video_file.exists() or video_file.stat().st_size == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested video file not found or has expired."
        )

    filename = "instagram_reel.mp4"
    job = jobs_db.get(valid_id)
    if job and job.get("video_metadata") and job["video_metadata"].get("filename"):
        filename = job["video_metadata"]["filename"]

    return FileResponse(
        path=str(video_file),
        media_type="video/mp4",
        filename=filename,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache, no-store, must-revalidate"
        }
    )


@router.get(
    "/download-video-fullscreen/{job_id}",
    summary="Download full-screen cropped MP4 video",
    description="Returns the cropped 16:9 full-screen MP4 video file as an attachment."
)
async def download_video_fullscreen(job_id: str):
    # Validate Job ID format
    try:
        valid_id = validate_job_id(job_id)
    except ValidationError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job ID.")

    job_dir = cleanup_service.get_job_dir(valid_id)
    video_file = job_dir / "video_fullscreen.mp4"

    if not video_file.exists() or video_file.stat().st_size == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Full-screen video file not found or has expired."
        )

    filename = "video_fullscreen.mp4"
    job = jobs_db.get(valid_id)
    if job and job.get("fullscreen_metadata") and job["fullscreen_metadata"].get("filename"):
        filename = job["fullscreen_metadata"]["filename"]

    return FileResponse(
        path=str(video_file),
        media_type="video/mp4",
        filename=filename,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache, no-store, must-revalidate"
        }
    )


@router.get(
    "/download/{job_id}",
    summary="Download converted MP3 audio",
    description="Returns the generated MP3 file as an attachment."
)
async def download_mp3(job_id: str):
    # Validate Job ID format
    try:
        valid_id = validate_job_id(job_id)
    except ValidationError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job ID.")

    job_dir = cleanup_service.get_job_dir(valid_id)
    mp3_file = job_dir / "output.mp3"

    if not mp3_file.exists() or mp3_file.stat().st_size == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested audio file not found or has expired."
        )

    filename = "instagram_reel_audio.mp3"
    job = jobs_db.get(valid_id)
    if job and job.get("metadata") and job["metadata"].get("filename"):
        filename = job["metadata"]["filename"]

    return FileResponse(
        path=str(mp3_file),
        media_type="audio/mpeg",
        filename=filename,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache, no-store, must-revalidate"
        }
    )
