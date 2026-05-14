import pytest

from src.application.use_cases.file_validator import (
    MagicBytesMismatchError,
    validate_magic_bytes,
)

# ─── Valid signatures ────────────────────────────────────────────────────────

def test_valid_png():
    content = b"\x89PNG\r\n\x1a\n" + b"rest-of-file"
    validate_magic_bytes(content, "image/png")  # must not raise


def test_valid_jpeg():
    content = b"\xff\xd8\xff\xe0" + b"rest-of-file"
    validate_magic_bytes(content, "image/jpeg")


def test_valid_jpg_alias():
    content = b"\xff\xd8\xff\xe1" + b"rest-of-file"
    validate_magic_bytes(content, "image/jpg")


def test_valid_pdf():
    content = b"%PDF-1.4\n rest-of-file"
    validate_magic_bytes(content, "application/pdf")


# ─── Invalid signatures (spoofed content type) ───────────────────────────────

def test_spoofed_png_declared_but_pdf_bytes():
    content = b"%PDF-1.4\n fake-pdf"
    with pytest.raises(MagicBytesMismatchError):
        validate_magic_bytes(content, "image/png")


def test_spoofed_pdf_declared_but_png_bytes():
    content = b"\x89PNG\r\n\x1a\n" + b"fake-png"
    with pytest.raises(MagicBytesMismatchError):
        validate_magic_bytes(content, "application/pdf")


def test_spoofed_jpeg_declared_but_text_content():
    content = b"GIF89a" + b"rest"
    with pytest.raises(MagicBytesMismatchError):
        validate_magic_bytes(content, "image/jpeg")


def test_empty_file_raises_for_known_type():
    with pytest.raises(MagicBytesMismatchError):
        validate_magic_bytes(b"", "image/png")


def test_unknown_content_type_is_noop():
    """Unknown types pass through — the allowlist check upstream handles them."""
    validate_magic_bytes(b"anything", "application/octet-stream")  # must not raise
