#!/usr/bin/env python3
"""Wait for a named job in the current workflow run to complete before proceeding.

Requires: gh CLI (pre-installed on GitHub-hosted runners)
Permissions: actions: read  (default for GITHUB_TOKEN)
"""

from __future__ import annotations

import argparse
import itertools
import json
import os
import subprocess
import sys
import time
from typing import Any


def main() -> None:
    parser = argparse.ArgumentParser(description="Wait for a GitHub Actions job to complete.")
    parser.add_argument("job_name", help="Name of the job to wait for")
    job_name = parser.parse_args().job_name
    repo = os.environ["GITHUB_REPOSITORY"]
    run_id = os.environ["GITHUB_RUN_ID"]
    cmd = ["gh", "api", f"/repos/{repo}/actions/runs/{run_id}/jobs", "--paginate", "--slurp"]
    print(f"Waiting for job {job_name!r} (run {run_id}) ...")
    deadline = time.monotonic() + 3600
    for interval in itertools.chain([0], itertools.repeat(15)):
        if time.monotonic() >= deadline:
            sys.exit(f"Timed out waiting for {job_name!r}.")
        if interval:
            print(f"  Sleeping {interval} seconds before retry ...")
            time.sleep(interval)
        print(f"Running {cmd}:")
        try:
            raw = subprocess.check_output(cmd, text=True, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            print(f"  Warning: gh api error ({e.stderr}).")
            continue
        jobs = [job for page in json.loads(raw) for job in page["jobs"]]
        job = find_job(jobs, name=job_name)
        if job is None:
            print(f"  Job not visible yet!")
            continue
        status = job["status"]  # queued | in_progress | completed
        print(f"  Job running with status={status}")
        if status != "completed":
            continue
        conclusion = job.get("conclusion")  # success | failure | cancelled | ...
        if conclusion == "success":
            print(f"Job {job_name!r} succeeded.")
            sys.exit(0)
        sys.exit(f"Job {job_name!r} ended with: {conclusion}")


def find_job(jobs: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    for job in jobs:
        if job["name"].rsplit("/", 1)[-1].strip() == name:
            return job
    return None


if __name__ == "__main__":
    main()
