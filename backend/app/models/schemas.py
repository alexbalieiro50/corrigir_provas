from typing import List, Optional

from pydantic import BaseModel, Field


class AnswerItem(BaseModel):
    question: int
    marked: Optional[str] = None
    correct: Optional[str] = None
    status: str  # "correct" | "wrong" | "blank" | "invalid"
    confidence: float


class PageResult(BaseModel):
    page: int = Field(1, description="Número da página (para PDFs com múltiplas páginas)")
    totalQuestions: int
    correct: int
    wrong: int
    blank: int
    invalid: int
    score: float
    answers: List[AnswerItem]
    processedImageBase64: Optional[str] = Field(
        None, description="Imagem da folha processada (PNG em base64), com marcações destacadas"
    )


class CorrectionResponse(BaseModel):
    pages: List[PageResult]
    # Campos "achatados" com o resultado da primeira página, para facilitar o
    # consumo no frontend do MVP (que assume 1 folha = 1 página, na maioria dos casos)
    totalQuestions: int
    correct: int
    wrong: int
    blank: int
    invalid: int
    score: float
    answers: List[AnswerItem]
    processedImageBase64: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str
    message: str
