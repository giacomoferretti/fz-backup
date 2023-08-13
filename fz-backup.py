#!/usr/bin/env python3

import argparse
import datetime
import pathlib

from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
)

from flipperzero_protobuf_py.flipperzero_protobuf.cli_helpers import *
from flipperzero_protobuf_py.flipperzero_protobuf.flipper_proto import FlipperProto

BASE_PATH = pathlib.Path(__file__).parent.resolve()

progress = Progress(
    TextColumn("[bold blue]{task.description}"),
    BarColumn(bar_width=None),
    TaskProgressColumn(),
    MofNCompleteColumn(),
    TimeRemainingColumn(),
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-o",
        "--output",
        help="Backup directory",
        dest="backup_directory",
    )
    args = parser.parse_args()

    # Connect to Flipper Zero
    proto = FlipperProto()

    if not args.backup_directory:
        args.backup_directory = (
            BASE_PATH
            / "backups"
            / (
                f'{proto.device_info["hardware_name"]}_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}'
            )
        )

    # Scan filesystem
    folders = []
    files = []
    queue = ["/int", "/ext"]

    while len(queue) > 0:
        target = queue.pop()
        folders.append(target)

        for x in proto.rpc_storage_list(target):
            if x.get("type") == "DIR":
                queue.append(str(pathlib.Path(target) / x.get("name")))

            if x.get("type") == "FILE":
                files.append(str(pathlib.Path(target) / x.get("name")))

    # Create folders
    for x in folders:
        (pathlib.Path(args.backup_directory) / x.lstrip("/")).mkdir(
            parents=True, exist_ok=True
        )

    # Backup files
    with progress:
        task = progress.add_task("Backing up...", total=len(files))

        for x in files:
            progress.print(f"Backing up {x}...")
            with open(pathlib.Path(args.backup_directory) / x.lstrip("/"), "wb") as f:
                f.write(proto.rpc_read(x))
            progress.update(task, advance=1)


if __name__ == "__main__":
    main()
