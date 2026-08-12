"""Converte páginas de um PDF em imagens para serem processadas pelo pipeline de OMR.

Usa PyMuPDF (fitz), que não depende de binários externos (como o Poppler),
facilitando a instalação em qualquer ambiente.
"""

from typing import List

from ..omr.exceptions import InvalidFileError, UnreadableImageError

RENDER_DPI = 200


def pdf_to_images(pdf_bytes: bytes) -> List[bytes]:
    """Converte cada página do PDF em uma imagem PNG (bytes).

    Se o PDF tiver 1 página, retorna uma lista com 1 item.
    Se tiver várias páginas, retorna uma imagem por página (processadas
    posteriormente em sequência pelo endpoint).
    """
    try:
        import fitz  # PyMuPDF
    except ImportError as e:
        raise InvalidFileError(
            "Suporte a PDF requer a biblioteca PyMuPDF. Instale com: pip install pymupdf"
        ) from e

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        raise UnreadableImageError("Não foi possível ler o arquivo PDF enviado.") from e

    if doc.page_count == 0:
        raise UnreadableImageError("O PDF enviado não contém páginas.")

    zoom = RENDER_DPI / 72.0
    matrix = fitz.Matrix(zoom, zoom)

    images: List[bytes] = []
    for page in doc:
        pix = page.get_pixmap(matrix=matrix)
        images.append(pix.tobytes("png"))

    doc.close()
    return images
