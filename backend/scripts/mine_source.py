"""Explore a source file to find citable content.

Companion tool for the ``source-mining`` skill: inspect a PDF or text file
under the ``sources/`` directory to locate the table of contents, index
entries, and page ranges worth embedding as cited excerpts.

Usage (paths are relative to SOURCES_DIR, default ``sources/``):

    python -m backend.scripts.mine_source book.pdf --info
    python -m backend.scripts.mine_source book.pdf --toc
    python -m backend.scripts.mine_source book.pdf --search "beamforming"
    python -m backend.scripts.mine_source book.pdf --pages 161-170
"""

import argparse
import sys

from pypdf import PdfReader

from backend.services.source_service import resolve_source_path


def _print_info(path_arg: str) -> None:
    """Print page count and document metadata."""
    file_path = resolve_source_path(path_arg)
    if file_path.suffix.lower() == ".pdf":
        reader = PdfReader(file_path)
        print(f"pages: {len(reader.pages)}")
        if reader.metadata:
            for key, value in reader.metadata.items():
                print(f"{key}: {value}")
    else:
        lines = file_path.read_text(encoding="utf-8").splitlines()
        print(f"lines: {len(lines)}")


def _print_toc(path_arg: str) -> None:
    """Print the PDF outline (bookmarks) with 1-indexed page numbers."""
    file_path = resolve_source_path(path_arg)
    if file_path.suffix.lower() != ".pdf":
        print("--toc is only available for PDF sources", file=sys.stderr)
        raise SystemExit(2)
    reader = PdfReader(file_path)

    def walk(entries: list[object], depth: int) -> None:
        for entry in entries:
            if isinstance(entry, list):
                walk(entry, depth + 1)
                continue
            title = getattr(entry, "title", "?")
            try:
                page_number = reader.get_destination_page_number(entry)  # type: ignore[arg-type]
            except (KeyError, ValueError, TypeError):
                page_number = None
            page = "?" if page_number is None else str(page_number + 1)
            print(f"{'  ' * depth}{title}  ·  p. {page}")

    outline = reader.outline
    if not outline:
        print("(no outline embedded — search for 'Contents' pages with --search)")
        return
    walk(list(outline), 0)


def _print_search(path_arg: str, term: str) -> None:
    """Print pages (or lines) whose text contains the term, case-insensitive."""
    file_path = resolve_source_path(path_arg)
    needle = term.lower()
    if file_path.suffix.lower() == ".pdf":
        reader = PdfReader(file_path)
        for number, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").lower()
            if needle in text:
                index = text.find(needle)
                snippet = text[max(0, index - 60) : index + 60].replace("\n", " ")
                print(f"p. {number}: …{snippet}…")
    else:
        for number, line in enumerate(file_path.read_text(encoding="utf-8").splitlines(), start=1):
            if needle in line.lower():
                print(f"line {number}: {line.strip()}")


def _print_pages(path_arg: str, page_range: str) -> None:
    """Print extracted text for an inclusive 1-indexed page (or line) range."""
    start_str, _, end_str = page_range.partition("-")
    start, end = int(start_str), int(end_str or start_str)
    file_path = resolve_source_path(path_arg)
    if file_path.suffix.lower() == ".pdf":
        reader = PdfReader(file_path)
        for number in range(start, min(end, len(reader.pages)) + 1):
            print(f"--- p. {number} ---")
            print(reader.pages[number - 1].extract_text() or "")
    else:
        lines = file_path.read_text(encoding="utf-8").splitlines()
        for number in range(start, min(end, len(lines)) + 1):
            print(f"{number}: {lines[number - 1]}")


def main() -> None:
    """Parse arguments and run the requested inspection."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="source file path, relative to SOURCES_DIR")
    parser.add_argument("--info", action="store_true", help="page count and metadata")
    parser.add_argument("--toc", action="store_true", help="print the PDF outline")
    parser.add_argument("--search", metavar="TERM", help="find pages containing TERM")
    parser.add_argument("--pages", metavar="A-B", help="print text for pages A through B")
    args = parser.parse_args()

    if args.info:
        _print_info(args.path)
    if args.toc:
        _print_toc(args.path)
    if args.search:
        _print_search(args.path, args.search)
    if args.pages:
        _print_pages(args.path, args.pages)
    if not (args.info or args.toc or args.search or args.pages):
        parser.print_help()


if __name__ == "__main__":
    main()
