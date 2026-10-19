import asyncio
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

import subprocess
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
            "format": "bestvideo[height<=1080]+bestaudio/best[height<=1080][acodec!=none]/best[acodec!=none]/bestaudio/bestvideo+bestaudio/best",
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
            # Extractor arguments for YouTube: use mobile client APIs to avoid bot blocks on datacenter IPs
            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "ios", "mweb", "web"]
                }
            }
        }

        # Provide direct ffmpeg binary location to yt-dlp
        if ffmpeg_bin:
            ydl_opts["ffmpeg_location"] = ffmpeg_bin

        # Optional cookie file for YouTube bot-detection bypass
        cookies_file = None
        if getattr(settings, "COOKIES_FILE", None) and Path(settings.COOKIES_FILE).is_file():
            cookies_file = settings.COOKIES_FILE
        elif (Path(settings.TEMP_DIR) / "cookies.txt").is_file():
            cookies_file = str(Path(settings.TEMP_DIR) / "cookies.txt")
        elif (Path(__file__).resolve().parent.parent.parent / "cookies.txt").is_file():
            cookies_file = str(Path(__file__).resolve().parent.parent.parent / "cookies.txt")
        elif getattr(settings, "YOUTUBE_COOKIES_TEXT", None) and settings.YOUTUBE_COOKIES_TEXT.strip():
            cookie_path = Path(settings.TEMP_DIR) / "youtube_cookies.txt"
            cookie_path.write_text(settings.YOUTUBE_COOKIES_TEXT.strip(), encoding="utf-8")
            cookies_file = str(cookie_path)

        if cookies_file:
            ydl_opts["cookiefile"] = cookies_file

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
                if platform == "youtube":
                    raise MediaRetrievalError(
                        "YouTube bot verification is active for this cloud server IP. "
                        "Please select 'Localhost' in Server Settings or supply YouTube cookies."
                    )
                else:
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

        # Locate downloaded input media file(s), ignoring partial temp files
        candidates = [
            f for f in output_dir.glob("input.*")
            if not f.name.endswith((".part", ".ytdl")) and f.is_file() and f.stat().st_size > 0
        ]
        if not candidates:
            raise MediaRetrievalError("Unable to retrieve the publicly accessible media.")

        merged_mp4 = output_dir / "input.mp4"
        if merged_mp4.exists() and merged_mp4.stat().st_size > 0:
            downloaded_file = merged_mp4
        else:
            # Fallback: if separate video and audio streams downloaded without automatic merging
            v_files = [f for f in candidates if any(k in f.name for k in ["v.", ".v", "video"])]
            a_files = [f for f in candidates if any(k in f.name for k in ["a.", ".a", "audio", "m4a", "webm", "opus"])]
            if v_files and a_files and ffmpeg_bin:
                try:
                    logger.info("Merging downloaded split video and audio streams via FFmpeg...")
                    subprocess.run(
                        [ffmpeg_bin, "-y", "-i", str(v_files[0]), "-i", str(a_files[0]), "-c:v", "copy", "-c:a", "aac", str(merged_mp4)],
                        capture_output=True,
                        timeout=60,
                        check=True
                    )
                    downloaded_file = merged_mp4 if (merged_mp4.exists() and merged_mp4.stat().st_size > 0) else candidates[0]
                except Exception as merge_err:
                    logger.warning(f"Fallback merge failed: {merge_err}")
                    downloaded_file = candidates[0]
            else:
                candidates.sort(key=lambda f: (1 if f.suffix.lower() == ".mp4" else 0, f.stat().st_size), reverse=True)
                downloaded_file = candidates[0]

        if downloaded_file.stat().st_size == 0:
            raise MediaRetrievalError("Downloaded media was empty.")

        if downloaded_file.stat().st_size > max_bytes:
            raise MediaRetrievalError(f"Video exceeds the maximum permitted size of {settings.MAX_DOWNLOAD_SIZE_MB}MB.")

        return downloaded_file, extracted_info


media_service = MediaService()
