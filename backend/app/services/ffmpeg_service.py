import logging
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple

from app.config import settings

logger = logging.getLogger(__name__)


class FFmpegError(Exception):
    pass


class NoAudioStreamError(FFmpegError):
    pass


class ConversionTimeoutError(FFmpegError):
    pass


class FFmpegService:
    def __init__(self):
        self._ffmpeg_bin: Optional[str] = None
        self._ffprobe_bin: Optional[str] = None
        try:
            self._ffmpeg_bin = self.get_ffmpeg_binary()
        except Exception:
            pass

    def get_ffmpeg_binary(self) -> str:
        """Finds the ffmpeg executable from settings, PATH, or imageio_ffmpeg."""
        if self._ffmpeg_bin and os.path.isfile(self._ffmpeg_bin):
            return self._ffmpeg_bin

        if settings.FFMPEG_PATH and os.path.isfile(settings.FFMPEG_PATH):
            self._ffmpeg_bin = settings.FFMPEG_PATH
            self._ensure_in_path(self._ffmpeg_bin)
            return self._ffmpeg_bin

        # 1. System PATH ffmpeg (installed in OS / Docker container with ffprobe)
        system_ffmpeg = shutil.which("ffmpeg")
        if system_ffmpeg and os.path.isfile(system_ffmpeg):
            self._ffmpeg_bin = system_ffmpeg
            return self._ffmpeg_bin

        # 2. imageio-ffmpeg fallback
        try:
            import imageio_ffmpeg
            exe = imageio_ffmpeg.get_ffmpeg_exe()
            if exe and os.path.isfile(exe):
                # Standardize as ffmpeg or ffmpeg.exe in a dedicated bin directory
                standard_exe = self._create_standard_ffmpeg_shim(exe)
                self._ffmpeg_bin = standard_exe
                self._ensure_in_path(standard_exe)
                return self._ffmpeg_bin
        except ImportError:
            pass

        raise FFmpegError("FFmpeg executable could not be found. Please ensure FFmpeg is installed.")

    def _ensure_in_path(self, bin_path: str):
        """Prepends the directory containing the binary to os.environ['PATH']."""
        try:
            bin_dir = str(Path(bin_path).resolve().parent)
            current_path = os.environ.get("PATH", "")
            if bin_dir not in current_path.split(os.pathsep):
                os.environ["PATH"] = bin_dir + os.pathsep + current_path
        except Exception as e:
            logger.debug(f"Could not prepend binary directory to PATH: {e}")

    def _create_standard_ffmpeg_shim(self, raw_exe: str) -> str:
        """Creates a standard 'ffmpeg' or 'ffmpeg.exe' copy/shim for tools like yt-dlp."""
        try:
            bin_dir = Path(settings.TEMP_DIR) / "bin"
            bin_dir.mkdir(parents=True, exist_ok=True)
            target_name = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
            target_file = bin_dir / target_name
            if not target_file.exists() or target_file.stat().st_size == 0:
                shutil.copyfile(raw_exe, target_file)
                try:
                    os.chmod(target_file, 0o755)
                except Exception:
                    pass
            return str(target_file)
        except Exception as e:
            logger.warning(f"Could not create standard ffmpeg shim: {e}. Using raw exe.")
            return raw_exe

    def get_ffprobe_binary(self) -> Optional[str]:
        """Finds ffprobe if available in settings, PATH, or adjacent to ffmpeg."""
        if self._ffprobe_bin and os.path.isfile(self._ffprobe_bin):
            return self._ffprobe_bin

        if settings.FFPROBE_PATH and os.path.isfile(settings.FFPROBE_PATH):
            self._ffprobe_bin = settings.FFPROBE_PATH
            return self._ffprobe_bin

        system_probe = shutil.which("ffprobe")
        if system_probe:
            self._ffprobe_bin = system_probe
            return self._ffprobe_bin

        try:
            ffmpeg_exe = self.get_ffmpeg_binary()
            adjacent_probe = Path(ffmpeg_exe).parent / ("ffprobe.exe" if os.name == "nt" else "ffprobe")
            if adjacent_probe.is_file():
                self._ffprobe_bin = str(adjacent_probe)
                return self._ffprobe_bin
        except Exception:
            pass

        return None

    def check_audio_stream_exists(self, video_path: Path) -> bool:
        """
        Verifies that the video file actually contains an audio stream.
        Uses ffprobe if available, or ffmpeg stream inspection.
        """
        ffprobe = self.get_ffprobe_binary()
        if ffprobe:
            cmd = [
                ffprobe,
                "-v", "error",
                "-select_streams", "a",
                "-show_entries", "stream=codec_type,codec_name",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(video_path)
            ]
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, errors="replace", check=False)
                if res.returncode == 0 and res.stdout.strip():
                    return True
                return False
            except Exception as e:
                logger.warning(f"ffprobe check failed: {e}. Falling back to ffmpeg inspection.")

        # Fallback using ffmpeg -i info inspection
        ffmpeg = self.get_ffmpeg_binary()
        cmd = [ffmpeg, "-i", str(video_path)]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, errors="replace", check=False)
            output = (res.stderr or "") + " " + (res.stdout or "")
            # Look for "Stream #...: Audio:"
            if re.search(r"Stream\s+#\d+:\d+.*:\s*Audio:", output, re.IGNORECASE) or ": Audio:" in output:
                return True
            return False
        except Exception as e:
            logger.error(f"Error inspecting media streams: {e}")
            raise FFmpegError("Unable to analyze video streams.")

    def extract_audio(
        self,
        input_video: Path,
        output_audio: Path,
        bitrate: str = "192k",
        filename: Optional[str] = None,
        title: Optional[str] = None,
        platform: Optional[str] = None
    ) -> Dict:
        """
        Extracts audio as MP3 using FFmpeg safely with subprocess argument lists.
        Validates presence of audio stream and returns metadata.
        """
        if not input_video.exists():
            raise FFmpegError("Input video file does not exist.")

        # Check audio stream existence
        has_audio = self.check_audio_stream_exists(input_video)
        if not has_audio:
            raise NoAudioStreamError("This video does not contain an audio stream.")

        ffmpeg = self.get_ffmpeg_binary()
        cmd = [
            ffmpeg,
            "-y",  # Overwrite output
            "-i", str(input_video),
            "-vn",  # No video
            "-map", "0:a:0",  # Select first audio stream
            "-codec:a", "libmp3lame",
            "-b:a", bitrate,
            str(output_audio)
        ]

        logger.info(f"Executing FFmpeg: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                errors="replace",
                timeout=settings.CONVERSION_TIMEOUT_SECONDS,
                check=False
            )
        except subprocess.TimeoutExpired:
            logger.error(f"FFmpeg conversion timed out after {settings.CONVERSION_TIMEOUT_SECONDS} seconds.")
            raise ConversionTimeoutError("Processing timed out. Please try again.")
        except Exception as e:
            logger.error(f"FFmpeg execution failed: {e}")
            raise FFmpegError("Audio conversion failed. Please try again.")

        if result.returncode != 0:
            logger.error(f"FFmpeg returned code {result.returncode}. Stderr: {result.stderr}")
            raise FFmpegError("Audio conversion failed. Please try again.")

        if not output_audio.exists() or output_audio.stat().st_size == 0:
            raise FFmpegError("Audio conversion produced an empty file. Please try again.")

        # Gather metadata
        metadata = self.get_media_metadata(
            output_audio,
            bitrate=bitrate,
            filename=filename,
            title=title,
            platform=platform
        )
        return metadata

    def get_media_metadata(
        self,
        audio_path: Path,
        bitrate: Optional[str] = None,
        filename: Optional[str] = None,
        title: Optional[str] = None,
        platform: Optional[str] = None
    ) -> Dict:
        """Calculates file size and duration metadata."""
        size_bytes = audio_path.stat().st_size if audio_path.exists() else 0
        human_size = self._format_size(size_bytes)
        
        duration_sec = self._probe_duration(audio_path)
        formatted_duration = self._format_duration(duration_sec) if duration_sec else "00:00"

        return {
            "filename": filename or "instagram_reel_audio.mp3",
            "title": title,
            "platform": platform or "instagram",
            "duration": formatted_duration,
            "duration_seconds": duration_sec,
            "bitrate": f"{bitrate.replace('k', '')} kbps" if bitrate else "192 kbps",
            "file_size": human_size,
            "file_size_bytes": size_bytes
        }

    def _probe_duration(self, file_path: Path) -> Optional[float]:
        """Probes the duration in seconds using ffprobe or ffmpeg."""
        ffprobe = self.get_ffprobe_binary()
        if ffprobe:
            cmd = [
                ffprobe,
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(file_path)
            ]
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, errors="replace", check=False)
                if res.returncode == 0 and res.stdout.strip():
                    return round(float(res.stdout.strip()), 2)
            except Exception:
                pass

        # Fallback ffmpeg stderr parse
        try:
            ffmpeg = self.get_ffmpeg_binary()
            res = subprocess.run([ffmpeg, "-i", str(file_path)], capture_output=True, text=True, errors="replace", check=False)
            output = (res.stderr or "") + " " + (res.stdout or "")
            match = re.search(r"Duration:\s+(\d+):(\d+):(\d+\.\d+)", output)
            if match:
                hours, mins, secs = match.groups()
                total = int(hours) * 3600 + int(mins) * 60 + float(secs)
                return round(total, 2)
        except Exception:
            pass

        return None

    @staticmethod
    def _format_size(num_bytes: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if num_bytes < 1024.0:
                return f"{num_bytes:.1f} {unit}" if unit != "B" else f"{num_bytes} B"
            num_bytes /= 1024.0
        return f"{num_bytes:.1f} TB"

    @staticmethod
    def _format_duration(seconds: Optional[float]) -> str:
        if not seconds or seconds < 0:
            return "00:00"
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"


    def detect_and_crop_black_bars(
        self,
        input_video: Path,
        output_video: Path,
        filename: Optional[str] = None,
        title: Optional[str] = None,
        platform: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Detects if video has heavy letterboxing (e.g., horizontal video padded inside a 9:16 vertical reel).
        If significant black bars are found, crops and formats it as a 16:9 widescreen MP4.
        """
        if not input_video.exists():
            return None

        ffmpeg = self.get_ffmpeg_binary()
        
        cmd = [
            ffmpeg,
            "-i", str(input_video),
            "-vf", "cropdetect=24:16:0",
            "-f", "null",
            "-max_muxing_queue_size", "1024",
            "-t", "4",
            "-"
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, errors="replace", check=False, timeout=20)
            stderr = res.stderr or ""
            crop_matches = re.findall(r"crop=(\d+):(\d+):(\d+):(\d+)", stderr)
            if not crop_matches:
                return None
            
            w, h, x, y = [int(v) for v in crop_matches[-1]]
            dim_match = re.search(r"Stream #.*Video:.* (\d{3,5})x(\d{3,5})", stderr)
            if not dim_match:
                return None
            
            orig_w, orig_h = int(dim_match.group(1)), int(dim_match.group(2))
            is_heavy_letterbox = (h <= 0.85 * orig_h) or (w <= 0.85 * orig_w)
            
            if not is_heavy_letterbox:
                return None
            
            w = w - (w % 2)
            h = h - (h % 2)
            x = x - (x % 2)
            y = y - (y % 2)

            logger.info(f"Detected letterboxing: {orig_w}x{orig_h} -> crop={w}:{h}:{x}:{y}. Generating full-screen 16:9 MP4.")
            
            crop_filter = f"crop={w}:{h}:{x}:{y},scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2"
            
            crop_cmd = [
                ffmpeg,
                "-y",
                "-i", str(input_video),
                "-vf", crop_filter,
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "22",
                "-c:a", "copy",
                str(output_video)
            ]
            
            subprocess.run(crop_cmd, capture_output=True, text=True, errors="replace", check=False, timeout=settings.CONVERSION_TIMEOUT_SECONDS)
            
            if output_video.exists() and output_video.stat().st_size > 0:
                size_bytes = output_video.stat().st_size
                return {
                    "filename": filename or "fullscreen_video.mp4",
                    "title": title,
                    "platform": platform,
                    "file_size": self._format_size(size_bytes),
                    "file_size_bytes": size_bytes
                }
        except Exception as e:
            logger.warning(f"Error during auto-crop detection: {e}")
            
        return None


ffmpeg_service = FFmpegService()
