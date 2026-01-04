"""Background job worker that processes the job queue."""

import asyncio
import signal
import sys
from datetime import datetime
from typing import Optional

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from src.db.sqlite_repository import get_repository
from src.db.models import JobDB
from api.jobs.handlers import execute_job


class JobWorker:
    """
    Background worker that polls the job queue and executes jobs.

    Usage:
        worker = JobWorker()
        await worker.run()

    Or run as a script:
        python -m api.jobs.worker
    """

    def __init__(self, poll_interval: float = 2.0, stuck_timeout_minutes: int = 15):
        self.poll_interval = poll_interval
        self.stuck_timeout_minutes = stuck_timeout_minutes
        self.running = False
        self._current_job: Optional[JobDB] = None

    def _cleanup_stuck_jobs(self):
        """Check for and fail any jobs that have been running too long."""
        repo = get_repository()
        failed_count = repo.fail_stuck_jobs(timeout_minutes=self.stuck_timeout_minutes)
        if failed_count > 0:
            print(f"[Worker] Marked {failed_count} stuck job(s) as failed")

    async def run(self):
        """Main worker loop."""
        self.running = True
        print(f"[Worker] Starting job worker (poll interval: {self.poll_interval}s)")

        # Handle graceful shutdown
        def signal_handler(sig, frame):
            print("\n[Worker] Shutting down gracefully...")
            self.running = False

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        while self.running:
            try:
                # Check for stuck jobs before processing new ones
                self._cleanup_stuck_jobs()
                await self.process_next_job()
            except Exception as e:
                print(f"[Worker] Error in main loop: {e}")

            if self.running:
                await asyncio.sleep(self.poll_interval)

        print("[Worker] Worker stopped")

    async def process_next_job(self):
        """Pick up and process the next pending job."""
        repo = get_repository()

        # Get next pending job
        job = repo.get_pending_job()
        if not job:
            return

        self._current_job = job
        print(f"[Worker] Processing job {job.id[:8]}... ({job.job_type})")

        try:
            # Mark as running
            repo.update_job_status(
                job.id,
                status="running",
                message="Starting...",
                progress=0,
            )

            # Execute the job
            result = await execute_job(job)

            # Mark as completed
            repo.update_job_status(
                job.id,
                status="completed",
                message="Done",
                progress=100,
                result=result,
            )
            print(f"[Worker] Job {job.id[:8]}... completed successfully")

        except Exception as e:
            error_msg = str(e)
            print(f"[Worker] Job {job.id[:8]}... failed: {error_msg}")

            # Check if we should retry
            job = repo.get_job(job.id)  # Refresh job state
            if job and job.attempts < job.max_attempts:
                # Re-queue for retry
                repo.update_job_status(
                    job.id,
                    status="pending",
                    message=f"Retry {job.attempts}/{job.max_attempts}: {error_msg}",
                    error=error_msg,
                )
                print(f"[Worker] Job {job.id[:8]}... queued for retry")
            else:
                # Mark as failed
                repo.update_job_status(
                    job.id,
                    status="failed",
                    message=f"Failed after {job.attempts} attempts",
                    error=error_msg,
                )

        finally:
            self._current_job = None

    async def run_once(self):
        """Process all pending jobs once, then exit."""
        print("[Worker] Running single pass...")
        repo = get_repository()

        processed = 0
        while True:
            job = repo.get_pending_job()
            if not job:
                break
            await self.process_next_job()
            processed += 1

        print(f"[Worker] Processed {processed} jobs")
        return processed


async def main():
    """Entry point for running the worker."""
    worker = JobWorker()
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
