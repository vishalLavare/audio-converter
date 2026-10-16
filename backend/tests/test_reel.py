import io
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routes.reel import jobs_db
from app.services.cleanup_service import CleanupService
from app.services.ffmpeg_service import (
    FFmpegService,
    NoAudioStreamError,
    ConversionTimeoutError,
    FFmpegError
)
from app.services.media_service import MediaRetrievalError
from app.utils.validators import (
    validate_and_normalize_reel_url,
    validate_job_id,
    ValidationError
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def temp_test_dir():
    d = Path(tempfile.mkdtemp())
    yield d
    shutil.rmtree(d, ignore_errors=True)


# 1. URL Validation Tests
class TestUrlValidation:
    def test_valid_instagram_reel_urls(self):
        valid_urls = [
            "https://www.instagram.com/reel/Daf2gF3vCzS/",
            "https://instagram.com/reel/Daf2gF3vCzS",
            "https://www.instagram.com/reels/Daf2gF3vCzS/",
            "https://www.instagram.com/reel/ABC123_xyz-/?utm_source=ig_web_copy_link&igsh=MzRlODBiNWFlZA==",
            "http://www.instagram.com/reel/Daf2gF3vCzS/"
        ]
        for u in valid_urls:
            norm, code = validate_and_normalize_reel_url(u)
            assert norm.startswith("https://www.instagram.com/reel/")
            assert code in ["Daf2gF3vCzS", "ABC123_xyz-"]

    def test_invalid_urls(self):
        invalid_urls = [
            "",
            "not-a-url",
            "ftp://instagram.com/reel/123",
            "https://www.instagram.com/p/12345/",  # standard post, not reel
            "https://www.instagram.com/stories/user/123/",
        ]
        for u in invalid_urls:
            with pytest.raises(ValidationError):
                validate_and_normalize_reel_url(u)

    def test_non_instagram_urls(self):
        external_urls = [
            "https://tiktok.com/@user/video/123456",
            "https://youtube.com/watch?v=123",
            "https://evil.com/reel/Daf2gF3vCzS/",
        ]
        for u in external_urls:
            with pytest.raises(ValidationError) as exc:
                validate_and_normalize_reel_url(u)
            assert "Unsupported domain" in str(exc.value.message)

    def test_ssrf_protection(self):
        ssrf_targets = [
            "http://localhost:8000/reel/123",
            "http://127.0.0.1/reel/123",
            "http://192.168.1.1/reel/123",
            "http://10.0.0.1/reel/123",
            "http://169.254.169.254/reel/123",
        ]
        for target in ssrf_targets:
            with pytest.raises(ValidationError):
                validate_and_normalize_reel_url(target)


# 2. Job ID & Bitrate Validation Tests
class TestJobAndBitrateValidation:
    def test_validate_job_id_success(self):
        good_id = str(uuid.uuid4())
        assert validate_job_id(good_id) == good_id

    def test_validate_job_id_path_traversal(self):
        dangerous_ids = [
            "../../etc/passwd",
            "..\\..\\windows\\system32",
            "invalid-uuid",
            "12345",
            ""
        ]
        for bad_id in dangerous_ids:
            with pytest.raises(ValidationError):
                validate_job_id(bad_id)

    def test_invalid_bitrate(self, client):
        res = client.post(
            "/api/reel/convert",
            json={"url": "https://www.instagram.com/reel/Daf2gF3vCzS/", "bitrate": "500k"}
        )
        assert res.status_code == 422  # Pydantic validation failure


# 3. API Workflow Tests
class TestReelEndpoints:
    def test_convert_endpoint_valid_request(self, client):
        with patch("app.routes.reel.process_conversion_task") as mock_task:
            res = client.post(
                "/api/reel/convert",
                json={"url": "https://www.instagram.com/reel/Daf2gF3vCzS/", "bitrate": "192k"}
            )
            assert res.status_code == 200
            data = res.json()
            assert "job_id" in data
            assert data["status"] == "processing"

    def test_convert_endpoint_invalid_url(self, client):
        res = client.post(
            "/api/reel/convert",
            json={"url": "https://evil.com/video/123", "bitrate": "192k"}
        )
        assert res.status_code == 400
        data = res.json()
        assert data["success"] is False
        assert "error" in data

    def test_status_endpoint_invalid_job_id(self, client):
        res = client.get("/api/reel/status/not-a-valid-uuid")
        assert res.status_code == 400
        assert res.json()["success"] is False

    def test_status_endpoint_job_not_found(self, client):
        random_uuid = str(uuid.uuid4())
        res = client.get(f"/api/reel/status/{random_uuid}")
        assert res.status_code == 404
        assert res.json()["success"] is False

    def test_status_endpoint_active_job(self, client):
        test_job_id = str(uuid.uuid4())
        jobs_db[test_job_id] = {
            "job_id": test_job_id,
            "status": "completed",
            "progress": 100,
            "current_step": "Done",
            "download_url": f"/api/reel/download/{test_job_id}",
            "metadata": {
                "filename": "instagram_reel_audio.mp3",
                "duration": "00:30",
                "bitrate": "192 kbps",
                "file_size": "1.2 MB",
                "file_size_bytes": 1258291
            },
            "error": None
        }
        res = client.get(f"/api/reel/status/{test_job_id}")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "completed"
        assert data["progress"] == 100
        assert data["download_url"] == f"/api/reel/download/{test_job_id}"
        assert data["metadata"]["duration"] == "00:30"

    def test_download_endpoint_file_exists(self, client, temp_test_dir):
        test_job_id = str(uuid.uuid4())
        with patch("app.routes.reel.cleanup_service.get_job_dir", return_value=temp_test_dir):
            mp3_file = temp_test_dir / "output.mp3"
            mp3_file.write_bytes(b"dummy mp3 data content")

            res = client.get(f"/api/reel/download/{test_job_id}")
            assert res.status_code == 200
            assert res.headers["content-type"] == "audio/mpeg"
            assert "attachment; filename=\"instagram_reel_audio.mp3\"" in res.headers["content-disposition"]
            assert res.content == b"dummy mp3 data content"

    def test_download_endpoint_not_found(self, client):
        random_uuid = str(uuid.uuid4())
        res = client.get(f"/api/reel/download/{random_uuid}")
        assert res.status_code == 404

    def test_download_video_endpoint_file_exists(self, client, temp_test_dir):
        test_job_id = str(uuid.uuid4())
        with patch("app.routes.reel.cleanup_service.get_job_dir", return_value=temp_test_dir):
            video_file = temp_test_dir / "video.mp4"
            video_file.write_bytes(b"dummy mp4 video content")

            res = client.get(f"/api/reel/download-video/{test_job_id}")
            assert res.status_code == 200
            assert res.headers["content-type"] == "video/mp4"
            assert "attachment; filename=\"instagram_reel.mp4\"" in res.headers["content-disposition"]
            assert res.content == b"dummy mp4 video content"

    def test_download_video_endpoint_not_found(self, client):
        random_uuid = str(uuid.uuid4())
        res = client.get(f"/api/reel/download-video/{random_uuid}")
        assert res.status_code == 404


# 4. Service Tests (FFmpeg, Media, Cleanup)
class TestServices:
    def test_cleanup_service(self, temp_test_dir):
        service = CleanupService(base_dir=str(temp_test_dir))
        job_id = str(uuid.uuid4())
        job_dir = service.create_job_dir(job_id)
        assert job_dir.exists()

        # Create dummy file inside
        (job_dir / "test.txt").write_text("hello")
        assert (job_dir / "test.txt").exists()

        # Test cleanup job
        assert service.cleanup_job(job_id) is True
        assert not job_dir.exists()

    def test_cleanup_expired_jobs(self, temp_test_dir):
        service = CleanupService(base_dir=str(temp_test_dir))
        old_dir = temp_test_dir / "old_job"
        old_dir.mkdir()
        
        # Artificially age the directory by modifying mtime
        old_time = 0
        os.utime(str(old_dir), (old_time, old_time))

        deleted = service.cleanup_expired_jobs(max_age_minutes=1)
        assert deleted == 1
        assert not old_dir.exists()

    def test_ffmpeg_no_audio_stream_raises(self, temp_test_dir):
        svc = FFmpegService()
        dummy_video = temp_test_dir / "silent.mp4"
        dummy_video.write_bytes(b"0" * 100)

        with patch.object(svc, "check_audio_stream_exists", return_value=False):
            with pytest.raises(NoAudioStreamError) as exc:
                svc.extract_audio(dummy_video, temp_test_dir / "output.mp3")
            assert "does not contain an audio stream" in str(exc.value)

    def test_ffmpeg_timeout_raises(self, temp_test_dir):
        svc = FFmpegService()
        dummy_video = temp_test_dir / "video.mp4"
        dummy_video.write_bytes(b"0" * 100)

        with patch.object(svc, "check_audio_stream_exists", return_value=True):
            import subprocess
            with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="ffmpeg", timeout=120)):
                with pytest.raises(ConversionTimeoutError) as exc:
                    svc.extract_audio(dummy_video, temp_test_dir / "output.mp3")
                assert "Processing timed out" in str(exc.value)


# 5. Multi-Platform Support Tests (YouTube, Facebook, Instagram)
class TestMultiPlatformSupport:
    def test_valid_youtube_urls(self):
        from app.utils.validators import validate_and_normalize_url
        valid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://www.youtube.com/shorts/dQw4w9WgXcQ",
            "https://music.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/watch?feature=share&v=dQw4w9WgXcQ",
        ]
        for u in valid_urls:
            norm, media_id, platform = validate_and_normalize_url(u, selected_platform="youtube")
            assert norm == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            assert media_id == "dQw4w9WgXcQ"
            assert platform == "youtube"

    def test_valid_facebook_urls(self):
        from app.utils.validators import validate_and_normalize_url
        valid_urls = [
            "https://www.facebook.com/reel/123456789/",
            "https://facebook.com/reel/123456789",
            "https://www.facebook.com/watch/?v=987654321",
            "https://fb.watch/abcdef123/",
            "https://www.facebook.com/share/r/abc123xyz/",
        ]
        for u in valid_urls:
            norm, media_id, platform = validate_and_normalize_url(u, selected_platform="facebook")
            assert platform == "facebook"
            assert "facebook.com" in norm or "fb.watch" in norm

    def test_platform_mismatch_raises(self):
        from app.utils.validators import validate_and_normalize_url, ValidationError
        # User selected Instagram but provided YouTube link
        with pytest.raises(ValidationError) as exc:
            validate_and_normalize_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ", selected_platform="instagram")
        assert "The entered link is from Youtube" in str(exc.value.message)
        assert "you selected Instagram" in str(exc.value.message)

        # User selected YouTube but provided Facebook link
        with pytest.raises(ValidationError) as exc2:
            validate_and_normalize_url("https://www.facebook.com/reel/123456789/", selected_platform="youtube")
        assert "The entered link is from Facebook" in str(exc2.value.message)

    def test_convert_endpoint_youtube_request(self, client):
        with patch("app.routes.reel.process_conversion_task") as mock_task:
            res = client.post(
                "/api/reel/convert",
                json={
                    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                    "platform": "youtube",
                    "bitrate": "320k"
                }
            )
            assert res.status_code == 200
            data = res.json()
            assert "job_id" in data
            assert data["status"] == "processing"

    def test_convert_endpoint_facebook_request(self, client):
        with patch("app.routes.reel.process_conversion_task") as mock_task:
            res = client.post(
                "/api/reel/convert",
                json={
                    "url": "https://www.facebook.com/reel/123456789/",
                    "platform": "facebook",
                    "bitrate": "256k"
                }
            )
            assert res.status_code == 200
            data = res.json()
            assert "job_id" in data
            assert data["status"] == "processing"

    def test_valid_instagram_post_urls_preserves_type(self):
        from app.utils.validators import validate_and_normalize_url
        norm, code, plat = validate_and_normalize_url("https://www.instagram.com/p/DecVCjfjYSX/", "instagram")
        assert plat == "instagram"
        assert norm == "https://www.instagram.com/p/DecVCjfjYSX/"
        assert code == "DecVCjfjYSX"

        norm_reel, code_reel, plat_reel = validate_and_normalize_url("https://www.instagram.com/reel/Daf2gF3vCzS/", "instagram")
        assert norm_reel == "https://www.instagram.com/reel/Daf2gF3vCzS/"

        norm_tv, code_tv, plat_tv = validate_and_normalize_url("https://www.instagram.com/tv/Daf2gF3vCzS/", "instagram")
        assert norm_tv == "https://www.instagram.com/tv/Daf2gF3vCzS/"

    def test_photo_only_post_error_handling(self, temp_test_dir):
        from app.services.media_service import media_service, MediaRetrievalError
        import yt_dlp
        with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
            mock_ydl = MagicMock()
            mock_ydl.extract_info.side_effect = yt_dlp.utils.DownloadError("ERROR: [Instagram] DecU3UcNbqz: No video formats found!")
            mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

            with pytest.raises(MediaRetrievalError) as exc_info:
                media_service._download_media_sync(
                    "https://www.instagram.com/p/DecVCjfjYSX/",
                    temp_test_dir,
                    platform="instagram"
                )
            assert "photos/images without a video or audio stream" in exc_info.value.message

