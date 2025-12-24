#!/usr/bin/env python3
"""
Run the background job worker.

Usage:
    python run_worker.py

The worker will poll for pending jobs and execute them.
Press Ctrl+C to stop gracefully.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from api.jobs.worker import JobWorker


async def main():
    worker = JobWorker(poll_interval=2.0)
    await worker.run()


if __name__ == "__main__":
    print("Starting job worker...")
    print("Press Ctrl+C to stop\n")
    asyncio.run(main())
