"""Seed Docker-managed application volumes without overwriting existing data."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def copy_missing(source: Path, target: Path) -> tuple[int, int]:
    target.mkdir(parents=True, exist_ok=True)
    if not source.exists():
        print(f"seed source does not exist, skipped: {source}")
        return 0, 0

    copied_files = 0
    skipped_files = 0
    for source_path in source.rglob("*"):
        relative_path = source_path.relative_to(source)
        target_path = target / relative_path
        if source_path.is_dir():
            target_path.mkdir(parents=True, exist_ok=True)
            continue
        if target_path.exists():
            skipped_files += 1
            continue
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
        copied_files += 1
    return copied_files, skipped_files


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-source", type=Path, required=True)
    parser.add_argument("--data-target", type=Path, required=True)
    parser.add_argument("--logs-source", type=Path, required=True)
    parser.add_argument("--logs-target", type=Path, required=True)
    args = parser.parse_args()

    for label, source, target in (
        ("data", args.data_source, args.data_target),
        ("logs", args.logs_source, args.logs_target),
    ):
        copied, skipped = copy_missing(source, target)
        print(f"{label}: copied={copied}, existing_skipped={skipped}")


if __name__ == "__main__":
    main()
