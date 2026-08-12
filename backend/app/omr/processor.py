"""
Pipeline de visão computacional (OMR) usando OpenCV.

Etapas:
  1. Carregar imagem
  2. Converter para escala de cinza
  3. Reduzir ruído (Gaussian Blur)
  4. Threshold (Otsu) + Canny
  5. Detectar contorno do cartão (maior contorno quadrangular)
  6. Corrigir perspectiva (warp para tamanho canônico do template)
  7. Localizar as bolhas (regiões do template, em coordenadas normalizadas)
  8. Calcular percentual de preenchimento de cada bolha
  9. Decidir a alternativa marcada por questão, com critério de confiança
 10. Retornar respostas + metadados para visualização
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

import cv2
import numpy as np

from .template import CardTemplate
from .exceptions import CardNotFoundError, UnreadableImageError, ProcessingError

# ---- Parâmetros de confiança (ajustáveis) --------------------------------
# Percentual mínimo de preenchimento (0..1) para considerar que uma bolha foi marcada.
FILL_THRESHOLD = 0.35
# Diferença mínima entre a 1ª e a 2ª bolha mais preenchida para considerar resposta
# única e inequívoca. Se a diferença for pequena e ambas passarem do threshold,
# consideramos marcação inválida (dupla marcação).
AMBIGUITY_MARGIN = 0.12


@dataclass
class BubbleReading:
    alternative: str
    fill_ratio: float
    center_px: Tuple[int, int]
    radius_px: int


@dataclass
class QuestionReading:
    question: int
    status: str  # "answered" | "blank" | "invalid"
    marked: Optional[str]
    bubbles: List[BubbleReading]


@dataclass
class OMRResult:
    readings: List[QuestionReading]
    warped_image: np.ndarray  # imagem corrigida (BGR), usada para visualização


def decode_image(file_bytes: bytes) -> np.ndarray:
    """Decodifica bytes de imagem (jpg/png) para um array OpenCV (BGR)."""
    arr = np.frombuffer(file_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise UnreadableImageError()
    return img


def _order_points(pts: np.ndarray) -> np.ndarray:
    """Ordena 4 pontos como [top-left, top-right, bottom-right, bottom-left]."""
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def _find_sheet_contour(gray: np.ndarray) -> Optional[np.ndarray]:
    """Localiza o maior contorno quadrangular da imagem, correspondente à folha inteira."""
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 30, 150)  # Canny levemente mais sensível
    edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) # RETR_EXTERNAL evita quadros internos
    if not contours:
        return None

    img_area = gray.shape[0] * gray.shape[1]
    candidates = []
    
    # Ordena por área do contorno
    for c in sorted(contours, key=cv2.contourArea, reverse=True)[:10]:
        area = cv2.contourArea(c)
        # Exige que seja ao menos 40% da imagem total para garantir que é a folha inteira, e não o cabeçalho
        if area < img_area * 0.40:
            continue
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            candidates.append(approx.reshape(4, 2))

    if candidates:
        return candidates[0]

    # Fallback: Usar o retângulo delimitador do maior contorno disponível
    largest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest) < img_area * 0.30:
        return None
    x, y, w, h = cv2.boundingRect(largest)
    return np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]])


def _warp_to_canonical(img: np.ndarray, quad: np.ndarray, width: int, height: int) -> np.ndarray:
    rect = _order_points(quad.astype("float32"))
    dst = np.array(
        [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
        dtype="float32",
    )
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(img, M, (width, height))
    return warped


def _bubble_fill_ratio(binary: np.ndarray, cx: int, cy: int, r: int) -> float:
    """Calcula a fração de pixels 'marcados' (brancos, após threshold invertido)
    dentro do círculo da bolha."""
    h, w = binary.shape
    x0, x1 = max(cx - r, 0), min(cx + r, w)
    y0, y1 = max(cy - r, 0), min(cy + r, h)
    if x1 <= x0 or y1 <= y0:
        return 0.0
    roi = binary[y0:y1, x0:x1]

    mask = np.zeros(roi.shape, dtype=np.uint8)
    cv2.circle(mask, (cx - x0, cy - y0), r, 255, -1)

    total = cv2.countNonZero(mask)
    if total == 0:
        return 0.0
    filled = cv2.countNonZero(cv2.bitwise_and(roi, mask))
    return filled / total


def process_sheet(img: np.ndarray, template: CardTemplate) -> OMRResult:
    """Executa o pipeline completo de OMR sobre a imagem do cartão-resposta."""
    if img is None or img.size == 0:
        raise UnreadableImageError()

    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    except cv2.error as e:
        raise UnreadableImageError() from e

    quad = _find_sheet_contour(gray)
    if quad is None:
        # Se não achou bordas (ex: imagem digitalizada rente), usa as 4 pontas da própria imagem
        h, w = gray.shape[:2]
        quad = np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]])

    try:
        warped = _warp_to_canonical(img, quad, template.canonical_width, template.canonical_height)
    except cv2.error as e:
        raise ProcessingError("Falha ao corrigir a perspectiva do cartão.") from e

    warped_gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    warped_gray = cv2.GaussianBlur(warped_gray, (3, 3), 0)

    # Threshold adaptativo de Otsu (invertido: marcas escuras -> branco)
    _, binary = cv2.threshold(warped_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    # Operação morfológica para remover ruído pontual e reforçar as marcações
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

    W, H = template.canonical_width, template.canonical_height
    by_question = template.regions_by_question()

    readings: List[QuestionReading] = []
    for q_num in sorted(by_question.keys()):
        bubbles_meta = by_question[q_num]
        bubble_readings: List[BubbleReading] = []
        for b in bubbles_meta:
            cx, cy = int(b.cx * W), int(b.cy * H)
            r = max(int(b.r * W), 4)
            ratio = _bubble_fill_ratio(binary, cx, cy, r)
            bubble_readings.append(
                BubbleReading(alternative=b.alternative, fill_ratio=ratio, center_px=(cx, cy), radius_px=r)
            )

        status, marked = _decide_answer(bubble_readings)
        readings.append(
            QuestionReading(question=q_num, status=status, marked=marked, bubbles=bubble_readings)
        )

    return OMRResult(readings=readings, warped_image=warped)


def _decide_answer(bubbles: List[BubbleReading]) -> Tuple[str, Optional[str]]:
    """Aplica o critério de confiança para decidir a resposta de uma questão.

    Regras:
      - Nenhuma bolha acima do FILL_THRESHOLD -> "blank" (sem resposta)
      - Exatamente uma bolha claramente acima das demais -> "answered"
      - Duas ou mais bolhas acima do threshold e próximas em preenchimento -> "invalid"
    """
    sorted_bubbles = sorted(bubbles, key=lambda b: b.fill_ratio, reverse=True)
    top = sorted_bubbles[0]
    second = sorted_bubbles[1] if len(sorted_bubbles) > 1 else None

    if top.fill_ratio < FILL_THRESHOLD:
        return "blank", None

    # Conta quantas bolhas estão "marcadas" (acima do threshold)
    marked_bubbles = [b for b in sorted_bubbles if b.fill_ratio >= FILL_THRESHOLD]

    if len(marked_bubbles) >= 2:
        diff = top.fill_ratio - second.fill_ratio
        if diff < AMBIGUITY_MARGIN:
            return "invalid", None
        # Uma domina claramente sobre as demais, mesmo com mais de uma acima do threshold
        return "answered", top.alternative

    return "answered", top.alternative
