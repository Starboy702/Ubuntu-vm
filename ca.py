#!/usr/bin/env python3
"""Rename filenames containing YYYY.MM.DD to YYYY-MM-DD after extracting a ZIP."""
import os
import re
import shutil
import argparse
import zipfile


# Task 2 
def extract_zip(infile: str, location: str) -> None:
    """
    Create destination folder if needed and extract all contents of a ZIP there.
    """
    if not os.path.exists(location):
        os.makedirs(location)

    with zipfile.ZipFile(infile, "r") as zf:
        zf.extractall(location)


# Task 3 
def rename_files(location: str) -> None:
    """
    Walk the location tree and rename any file whose name contains a date
    in YYYY.MM.DD to the format YYYY-MM-DD. Other parts of the name are preserved.
    """
   
    date_pattern = re.compile(r"(\d{4})\.(\d{1,2})\.(\d{1,2})")

    for root, _, files in os.walk(location):
        for fname in files:
            m = date_pattern.search(fname)
            if not m:
                continue

          
            yyyy, mm, dd = m.group(1), int(m.group(2)), int(m.group(3))
            new_fname = date_pattern.sub(f"{yyyy}-{mm:02d}-{dd:02d}", fname)

            if new_fname != fname:
                old_path = os.path.join(root, fname)
                new_path = os.path.join(root, new_fname)
                print(f'Renaming "{old_path}" to "{new_path}"...')
                shutil.move(old_path, new_path)


# Task 1 
def parse_args():
    parser = argparse.ArgumentParser(
        prog="ca.py",
        description="Extract a ZIP and rename files from YYYY.MM.DD to YYYY-MM-DD format.",
    )
    parser.add_argument(
        "-i", "--ifile", required=True, metavar="file.zip", help="Input ZIP file"
    )
    parser.add_argument(
        "-l", "--location", required=True, metavar="extract folder",
        help="Destination folder to extract files into"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    extract_zip(args.ifile, args.location)   # Task 2
    rename_files(args.location)              # Task 3


if __name__ == "__main__":
    main()
