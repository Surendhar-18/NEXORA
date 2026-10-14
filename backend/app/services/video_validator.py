import os
from pathlib import Path
from typing import Tuple

ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}

def check_video_magic_bytes(header: bytes) -> Tuple[bool, str]:
    """
    Validates binary header against known video container signatures.
    Returns (is_valid, detected_format).
    """
    if len(header) < 12:
        return False, "file_too_small"

    # 1. MP4 / MOV (ISO Base Media File Format)
    # Typically begins with 4 bytes size, followed by 'ftyp'
    if header[4:8] == b"ftyp":
        major_brand = header[8:12]
        return True, f"isom/{major_brand.decode('ascii', errors='ignore').strip()}"

    # QuickTime MOV variation starting with moov/mdat/wide
    if header[4:8] in (b"moov", b"mdat", b"wide"):
        return True, "mov"

    # 2. AVI (RIFF container with 'AVI ' form type)
    if header[:4] == b"RIFF" and header[8:12] == b"AVI ":
        return True, "avi"

    # 3. MKV / WebM (EBML header \x1a\x45\xdf\xa3)
    if header[:4] == b"\x1a\x45\xdf\xa3":
        return True, "matroska"

    # Rejection: Check for Windows executable (MZ), ZIP, ELF, Shell, HTML
    if header[:2] == b"MZ":
        return False, "executable_pe"
    if header[:4] == b"\x7fELF":
        return False, "executable_elf"
    if header[:4] == b"PK\x03\x04":
        return False, "zip_archive"
    if header.startswith(b"<!DOCTYPE") or header.startswith(b"<html"):
        return False, "html_document"
    if header.startswith(b"#!/"):
        return False, "script"

    return False, "unsupported_binary_header"

def sanitize_filename(raw_filename: str) -> str:
    """Strips path traversal elements and normalizes filename."""
    base_name = Path(raw_filename).name
    # Keep only safe alphanumeric, hyphen, underscore, and dot
    clean_name = "".join(c for c in base_name if c.isalnum() or c in ("-", "_", "."))
    return clean_name or "uploaded_video.mp4"
