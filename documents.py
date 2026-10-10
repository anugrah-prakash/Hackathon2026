"""Decode files locally; never execute document content or follow embedded links."""
from io import BytesIO
import warnings
from PIL import Image, ImageOps
import fitz

MAX_BYTES = 20 * 1024 * 1024
MAX_PAGES = 6


def pages(data: bytes) -> list[bytes]:
    if not data or len(data) > MAX_BYTES:
        raise ValueError('Choose a nonempty file smaller than 20 MB.')
    if data.startswith(b'%PDF-'):
        with fitz.open(stream=data, filetype='pdf') as doc:
            if doc.needs_pass or not 1 <= len(doc) <= MAX_PAGES:
                raise ValueError('Use an unlocked PDF with 1–6 pages; include the complete letter.')
            result = []
            for page in doc:
                rect = page.rect
                if min(rect.width, rect.height) <= 0:
                    raise ValueError('Invalid PDF page size.')
                scale = min(2.5, 2400 / max(rect.width, rect.height))
                result.append(page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False).tobytes('png'))
            return result
    with warnings.catch_warnings():
        warnings.simplefilter('error', Image.DecompressionBombWarning)
        with Image.open(BytesIO(data)) as im:
            if im.format not in ('PNG', 'JPEG', 'WEBP') or getattr(im, 'n_frames', 1) != 1:
                raise ValueError('Use a single-frame JPG, PNG or WebP image, or a PDF.')
            im = ImageOps.exif_transpose(im).convert('RGB')
            im.thumbnail((2400, 2400))
            out = BytesIO()
            im.save(out, format='PNG')
            return [out.getvalue()]


def embedded_text(data: bytes) -> str | None:
    """Prefer a PDF's text layer only when every page contains usable text.

    This is not proof of visual completeness; the user still checks the preview.
    Mixed/scanned PDFs fall back to image transcription for all pages.
    """
    if not data or len(data) > MAX_BYTES or not data.startswith(b'%PDF-'):
        return None
    with fitz.open(stream=data, filetype='pdf') as doc:
        if doc.needs_pass or not 1 <= len(doc) <= MAX_PAGES:
            return None
        texts = [page.get_text('text', sort=True).strip() for page in doc]
        if any(len(t) < 80 or '\ufffd' in t for t in texts):
            return None
        return '\n\n'.join(texts)
