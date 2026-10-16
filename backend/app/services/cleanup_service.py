import asyncio
import logging
import os
import shutil
import time
from pathlib import Path
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


class CleanupService:
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir or settings.TEMP_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_job_dir(self, job_id: str) -> Path:
        """Returns the absolute Path for a given job ID."""
        return self.base_dir / job_id

    def create_job_dir(self, job_id: str) -> Path:
        """Creates and returns the job directory."""
        job_dir = self.get_job_dir(job_id)
        job_dir.mkdir(parents=True, exist_ok=True)
        return job_dir

    def cleanup_job(self, job_id: str) -> bool:
        """Removes the directory for a specific job."""
        job_dir = self.get_job_dir(job_id)
        if job_dir.exists():
            try:
                shutil.rmtree(job_dir, ignore_errors=True)
                logger.info(f"Cleaned up job directory: {job_dir}")
                return True
            except Exception as e:
                logger.error(f"Error cleaning up job {job_id}: {e}")
        return False

    def cleanup_expired_jobs(self, max_age_minutes: Optional[int] = None) -> int:
        """
        Deletes job directories that are older than max_age_minutes.
        Returns the count of deleted directories.
        """
        max_age = max_age_minutes or settings.CLEANUP_AFTER_MINUTES
        threshold_seconds = max_age * 60
        now = time.time()
        deleted_count = 0

        if not self.base_dir.exists():
            return 0

        for item in self.base_dir.iterdir():
            if item.is_dir():
                try:
                    mtime = item.stat().st_mtime
                    if (now - mtime) > threshold_seconds:
                        shutil.rmtree(item, ignore_errors=True)
                        deleted_count += 1
                        logger.info(f"Cleaned up expired directory: {item.name}")
                except Exception as e:
                    logger.warning(f"Could not inspect or remove {item}: {e}")

        return deleted_count

    async def start_periodic_cleanup(self, interval_seconds: int = 300):
        """Asynchronous background loop to periodically remove expired files."""
        while True:
            try:
                await asyncio.sleep(interval_seconds)
                deleted = self.cleanup_expired_jobs()
                if deleted > 0:
                    logger.info(f"Periodic cleanup removed {deleted} expired job directory(s).")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error during periodic cleanup: {e}")


cleanup_service = CleanupService()
