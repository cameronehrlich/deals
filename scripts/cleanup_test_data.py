#!/usr/bin/env python3
"""Clean up test data from the database.

Usage:
    python scripts/cleanup_test_data.py [--dry-run]

Options:
    --dry-run    Show what would be deleted without actually deleting
"""

import sys
import argparse

# Add project root to path
sys.path.insert(0, ".")

from src.db.sqlite_repository import get_repository
from src.db.models import SavedPropertyDB, JobDB


def cleanup_test_data(dry_run: bool = False) -> dict:
    """Remove test data from the database.

    Test data is identified by:
    - Addresses containing "Test" (case insensitive)
    - Addresses starting with "123" and containing common test patterns
    - Properties with source="test"
    """
    repo = get_repository()
    results = {"properties": 0, "jobs": 0}

    # Find test properties
    test_properties = repo.session.query(SavedPropertyDB).filter(
        (SavedPropertyDB.address.ilike("%test%")) |
        (SavedPropertyDB.source == "test") |
        (SavedPropertyDB.address.ilike("123 %") & SavedPropertyDB.city.ilike("%test%"))
    ).all()

    if test_properties:
        print(f"\nFound {len(test_properties)} test properties:")
        for prop in test_properties:
            print(f"  - {prop.id[:20]}... | {prop.address}, {prop.city} | {prop.created_at}")

        if not dry_run:
            for prop in test_properties:
                repo.session.delete(prop)
            repo.session.commit()
            results["properties"] = len(test_properties)
            print(f"\nDeleted {len(test_properties)} test properties")
        else:
            print(f"\n[DRY RUN] Would delete {len(test_properties)} test properties")
    else:
        print("\nNo test properties found")

    # Find test jobs (jobs with test property IDs)
    test_jobs = repo.session.query(JobDB).filter(
        JobDB.payload.contains('"test"')
    ).all()

    if test_jobs:
        print(f"\nFound {len(test_jobs)} test jobs:")
        for job in test_jobs:
            print(f"  - {job.id[:20]}... | {job.job_type} | {job.status}")

        if not dry_run:
            for job in test_jobs:
                repo.session.delete(job)
            repo.session.commit()
            results["jobs"] = len(test_jobs)
            print(f"\nDeleted {len(test_jobs)} test jobs")
        else:
            print(f"\n[DRY RUN] Would delete {len(test_jobs)} test jobs")
    else:
        print("\nNo test jobs found")

    repo.close()
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean up test data from the database")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without deleting")
    args = parser.parse_args()

    print("=" * 50)
    print("Test Data Cleanup")
    print("=" * 50)

    results = cleanup_test_data(dry_run=args.dry_run)

    print("\n" + "=" * 50)
    if args.dry_run:
        print("DRY RUN COMPLETE - No data was deleted")
    else:
        print(f"Cleanup complete: {results['properties']} properties, {results['jobs']} jobs deleted")
    print("=" * 50)
