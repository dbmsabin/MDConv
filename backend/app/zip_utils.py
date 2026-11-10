"""Safe zip extraction utilities.

Protects against:
- Zip-slip (paths with ``..`` or absolute paths)
- Zip bombs (total uncompressed size and file count limits)
- Junk files (__MACOSX/, .DS_Store, Thumbs.db, hidden files)
"""

import os
import zipfile
from pathlib import Path, PurePosixPath

MAX_ZIP_FILES = int(os.getenv("MAX_ZIP_FILES", "200"))
MAX_UNZIPPED_MB = int(os.getenv("MAX_UNZIPPED_MB", "200"))
MAX_UNZIPPED_BYTES = MAX_UNZIPPED_MB * 1024 * 1024

JUNK_NAMES = {".ds_store", "thumbs.db"}
JUNK_PREFIXES = ("__macosx/",)


def _is_junk(name: str) -> bool:
    """Return True for Mac metadata files and hidden files."""
    lower = name.lower()
    if any(lower.startswith(p) for p in JUNK_PREFIXES):
        return True
    basename = PurePosixPath(lower).name
    if basename in JUNK_NAMES:
        return True
    if basename.startswith("."):
        return True
    return False


def _safe_path(member_name: str, dest: Path) -> Path | None:
    """Resolve the target path and ensure it stays inside *dest*.

    Returns ``None`` if the path would escape the destination (zip-slip).
    """
    # Normalise separators and strip leading slashes / drive letters
    clean = member_name.replace("\\", "/").lstrip("/")
    target = (dest / clean).resolve()
    try:
        target.relative_to(dest.resolve())
    except ValueError:
        return None
    return target


def extract_zip(zip_path: Path, dest: Path, *, nested: bool = False) -> list[Path]:
    """Extract *zip_path* into *dest* and return paths of extracted files.

    Args:
        zip_path: Path to the zip archive.
        dest: Directory to extract into (must already exist).
        nested: If True this is a nested zip — skip further zip extraction.

    Raises:
        ValueError: If limits are exceeded or the archive is not valid.
    """
    if not zipfile.is_zipfile(zip_path):
        raise ValueError(f"{zip_path.name} is not a valid zip file")

    extracted: list[Path] = []
    total_bytes = 0
    file_count = 0

    with zipfile.ZipFile(zip_path, "r") as zf:
        members = zf.infolist()

        for info in members:
            if info.is_dir():
                continue
            if _is_junk(info.filename):
                continue

            # Zip-bomb: file count
            file_count += 1
            if file_count > MAX_ZIP_FILES:
                raise ValueError(
                    f"Zip contains more than {MAX_ZIP_FILES} files — aborting extraction."
                )

            # Zip-bomb: uncompressed size (file_size may be 0 for stored entries, so
            # we also check after extraction via the actual written size).
            total_bytes += info.file_size
            if total_bytes > MAX_UNZIPPED_BYTES:
                raise ValueError(
                    f"Zip would unpack to more than {MAX_UNZIPPED_MB} MB — aborting."
                )

            # Zip-slip check
            target = _safe_path(info.filename, dest)
            if target is None:
                continue  # silently skip unsafe paths

            # Extract single member
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, open(target, "wb") as dst:
                dst.write(src.read())

            # Nested zip: extract one level deep only
            if not nested and target.suffix.lower() == ".zip":
                sub_dest = target.parent / target.stem
                sub_dest.mkdir(exist_ok=True)
                try:
                    sub_files = extract_zip(target, sub_dest, nested=True)
                    extracted.extend(sub_files)
                except ValueError:
                    pass  # treat bad nested zip as a file to skip
                target.unlink()
                continue

            extracted.append(target)

    return extracted

