import base64
import logging
from typing import List

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import JSONResponse

from ..models.schemas import AnswerItem, CorrectionResponse, PageResult
from ..omr.exceptions import OMRError, InvalidFileError
from ..omr.grading import grade
from ..omr.processor import decode_image, process_sheet
from ..omr.template import get_template
from ..omr.visualization import encode_png, render_result_image
from ..services.pdf_service import pdf_to_images
from ..utils.answer_key_parser import parse_answer_key

logger = logging.getLogger("omr_corrector")

router = APIRouter(prefix="/api", tags=["omr"])

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "pdf"}
MAX_FILE_SIZE_MB = 20


def _get_extension(filename: str) -> str:
    if not filename or "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/correct", response_model=CorrectionResponse, responses={400: {"model": None}})
async def correct(
    file: UploadFile = File(..., description="Imagem (jpg/png) ou PDF do cartão-resposta preenchido"),
    answer_key: str = Form(..., description="Gabarito no formato '1-A\\n2-C\\n...'"),
    template_name: str = Form("default_45", description="Nome do template do cartão"),
):
    try:
        ext = _get_extension(file.filename or "")
        if ext not in ALLOWED_EXTENSIONS:
            raise InvalidFileError(
                f"Formato '.{ext}' não suportado. Envie um arquivo JPG, JPEG, PNG ou PDF."
            )

        file_bytes = await file.read()
        if not file_bytes:
            raise InvalidFileError("Arquivo vazio.")
        if len(file_bytes) > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise InvalidFileError(f"Arquivo maior que {MAX_FILE_SIZE_MB}MB.")

        key = parse_answer_key(answer_key)
        template = get_template(template_name)

        # Monta a lista de imagens a processar (1 para jpg/png, N para PDF multi-página)
        if ext == "pdf":
            page_images = pdf_to_images(file_bytes)
        else:
            page_images = [file_bytes]

        pages: List[PageResult] = []
        for idx, img_bytes in enumerate(page_images, start=1):
            img = decode_image(img_bytes)
            result = process_sheet(img, template)
            summary = grade(result.readings, key)
            vis = render_result_image(result.warped_image, result.readings, summary.results)
            vis_png = encode_png(vis)
            vis_b64 = base64.b64encode(vis_png).decode("ascii")

            answers = [
                AnswerItem(
                    question=r.question,
                    marked=r.marked,
                    correct=r.correct_answer,
                    status=r.status,
                    confidence=r.confidence,
                )
                for r in summary.results
            ]

            pages.append(
                PageResult(
                    page=idx,
                    totalQuestions=summary.total_questions,
                    correct=summary.correct,
                    wrong=summary.wrong,
                    blank=summary.blank,
                    invalid=summary.invalid,
                    score=summary.score,
                    answers=answers,
                    processedImageBase64=vis_b64,
                )
            )

        first = pages[0]
        response = CorrectionResponse(
            pages=pages,
            totalQuestions=first.totalQuestions,
            correct=first.correct,
            wrong=first.wrong,
            blank=first.blank,
            invalid=first.invalid,
            score=first.score,
            answers=first.answers,
            processedImageBase64=first.processedImageBase64,
        )
        return response

    except OMRError as e:
        # Erros esperados: mensagem segura para o usuário, log técnico no backend
        logger.warning("Erro OMR (%s): %s", e.code, e.message)
        return JSONResponse(status_code=400, content={"error": e.code, "message": e.message})
    except Exception as e:
        # Erros inesperados: nunca expor stack trace ao usuário
        logger.exception("Erro inesperado ao processar cartão-resposta")
        return JSONResponse(
            status_code=500,
            content={"error": "internal_error", "message": "Erro interno ao processar o cartão-resposta."},
        )
