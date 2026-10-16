import asyncio
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

from app.config import settings

logger = logging.getLogger(__name__)


class MediaRetrievalError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class MediaService:
    def __init__(self):
        pass

    async def retrieve_public_media(
        self,
        normalized_url: str,
        output_dir: Path,
        platform: str = "auto"
    ) -> Tuple[Path, Dict]:
        """
        Downloads publicly accessible media from Instagram, YouTube, or Facebook
        without authentication bypass, DRM defeat, or illegal scraping.
        
        Returns:
            Tuple of (downloaded_file_path, extracted_info_dict)
        """
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(self._download_media_sync, normalized_url, output_dir, platform),
                timeout=float(settings.DOWNLOAD_TIMEOUT_SECONDS)
            )
        except asyncio.TimeoutError:
            logger.warning(f"Download timed out for URL: {normalized_url}")
            raise MediaRetrievalError("Processing timed out. Please try again.")

    async def retrieve_public_reel(self, normalized_url: str, output_dir: Path) -> Path:
        """
        Backward compatible method for Instagram Reels.
        """
        file_path, _ = await self.retrieve_public_media(normalized_url, output_dir, platform="instagram")
        return file_path

    def _download_media_sync(self, normalized_url: str, output_dir: Path, platform: str = "auto") -> Tuple[Path, Dict]:
        output_template = str(output_dir / "input.%(ext)s")
        max_bytes = settings.MAX_DOWNLOAD_SIZE_MB * 1024 * 1024

        try:
            import yt_dlp
        except ImportError:
            raise MediaRetrievalError("Media extractor service is unavailable.")

        from app.services.ffmpeg_service import ffmpeg_service
        ffmpeg_bin = None
        try:
            ffmpeg_bin = ffmpeg_service.get_ffmpeg_binary()
        except Exception:
            pass

        ydl_opts = {
            "outtmpl": output_template,
            "format": "bestvideo[height<=1080]+bestaudio/best[height<=1080][acodec!=none]/best[acodec!=none]/bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "max_filesize": max_bytes,
            "socket_timeout": 30,
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": False,
            "noplaylist": True,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            },
        }
        if ffmpeg_bin:
            # yt-dlp locates both ffmpeg and ffprobe if given the directory
            ydl_opts["ffmpeg_location"] = str(Path(ffmpeg_bin).parent)

        extracted_info = {}
        platform_label = platform.capitalize() if platform and platform != "auto" else "platform"

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(normalized_url, download=True)
                if not info:
                    raise MediaRetrievalError(
                        f"Unable to access this public {platform_label} media. "
                        "Please verify that the content is publicly accessible."
                    )
                extracted_info = {
                    "title": info.get("title"),
                    "duration": info.get("duration"),
                    "uploader": info.get("uploader"),
                    "thumbnail": info.get("thumbnail"),
                    "id": info.get("id"),
                }
        except yt_dlp.utils.MaxDownloadsReached:
            raise MediaRetrievalError(f"Video exceeds the maximum permitted size of {settings.MAX_DOWNLOAD_SIZE_MB}MB.")
        except yt_dlp.utils.DownloadError as de:
            err_msg = str(de).lower()
            logger.info(f"yt-dlp download error for {normalized_url}: {de}")

            if "private" in err_msg:
                raise MediaRetrievalError(f"Private {platform_label} content is not accessible.")
            elif any(k in err_msg for k in ["login", "checkpoint", "auth", "sign in", "confirm you're not a bot"]):
                raise MediaRetrievalError(
                    f"Unable to access this {platform_label} video. "
                    "Please verify that the link is publicly accessible without login requirements."
                )
            elif any(k in err_msg for k in ["no video formats", "no formats found", "no video", "has no video", "no media found"]):
                raise MediaRetrievalError(
                    f"This {platform_label} post contains only photos/images without a video or audio stream. Only video posts and reels can be converted."
                )
            elif any(k in err_msg for k in ["not found", "404", "unavailable", "does not exist", "deleted"]):
                raise MediaRetrievalError(f"This {platform_label} video is unavailable or has been removed.")
            elif any(k in err_msg for k in ["timed out", "timeout"]):
                raise MediaRetrievalError("Processing timed out. Please try again.")
            elif "max-filesize" in err_msg or "too large" in err_msg:
                raise MediaRetrievalError(f"Video exceeds the maximum permitted size of {settings.MAX_DOWNLOAD_SIZE_MB}MB.")
            else:
                raise MediaRetrievalError(
                    f"Unable to access this public {platform_label} media. Please check the URL and try again."
                )
        except Exception as e:
            logger.error(f"Unexpected error while retrieving media: {e}")
            raise MediaRetrievalError(
                f"Unable to process this {platform_label} media. Please check the link."
            )

        # Locate downloaded input video file
        candidate_files = list(output_dir.glob("input.*"))
        if not candidate_files:
            raise MediaRetrievalError("Unable to retrieve the publicly accessible media.")

        downloaded_file = candidate_files[0]
        if downloaded_file.stat().st_size == 0:
            raise MediaRetrievalError("Downloaded media was empty.")

        if downloaded_file.stat().st_size > max_bytes:
            raise MediaRetrievalError(f"Video exceeds the maximum permitted size of {settings.MAX_DOWNLOAD_SIZE_MB}MB.")

        return downloaded_file, extracted_info


media_service = MediaService()
