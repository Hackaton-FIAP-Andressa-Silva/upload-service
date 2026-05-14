"""Magic-bytes (file signature) validation for accepted file types.

Validates the actual binary content of a file instead of trusting the
client-supplied Content-Type header alone, preventing MIME-type spoofing.
"""
from typing import Tuple

# (content_type, magic_signature, byte_offset)
_SIGNATURES: Tuple[Tuple[str, bytes, int], ...] = (
    ("image/png",       b"\x89PNG\r\n\x1a\n",  0),
    ("image/jpeg",      b"\xff\xd8\xff",         0),
    ("image/jpg",       b"\xff\xd8\xff",         0),
    ("application/pdf", b"%PDF",                 0),
)


class MagicBytesMismatchError(Exception):
    """Raised when file magic bytes don't match the declared content type."""


def validate_magic_bytes(file_content: bytes, declared_content_type: str) -> None:
    """Verify that *file_content* starts with the expected magic bytes for
    *declared_content_type*.

    Raises:
        MagicBytesMismatchError: if the file's signature doesn't match its
            declared type (e.g., a PE executable renamed to .png).
    """
    for content_type, signature, offset in _SIGNATURES:
        if content_type == declared_content_type:
            chunk = file_content[offset: offset + len(signature)]
            if chunk != signature:
                raise MagicBytesMismatchError(
                    f"File content does not match declared type '{declared_content_type}'. "
                    "Upload a valid image or PDF file."
                )
            return
    # No known signature for this type — the content-type check upstream
    # will reject unsupported types before this point, so this is a safe no-op.
