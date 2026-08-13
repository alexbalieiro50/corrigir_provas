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

# Dimensão máxima (maior lado, em px) da imagem de ENTRADA antes de processar.
# Fotos de celular costumam vir com 3000-4000px; isso deixa a detecção de
# contorno mais lenta sem ganho de qualidade, já que a folha corrigida é
# sempre reamostrada para o tamanho canônico do template (ex.: 1000x1400).
MAX_INPUT_DIM = 1600

# ---- Parâmetros de confiança (ajustáveis) --------------------------------
# Percentual mínimo de preenchimento (0..1) para considerar que uma bolha foi marcada.
# Reduzido em relação à primeira versão (que usava um threshold binário único
# para a folha inteira) porque a medida agora é uma pontuação contínua de tinta
# por bolha — marcações de caneta mais fracas produzem valores mais baixos, mas
# ainda claramente acima do "ruído" de uma bolha vazia (tipicamente < 0.1).
FILL_THRESHOLD = 0.30
# Diferença mínima entre a 1ª e a 2ª bolha mais preenchida para considerar resposta
# única e inequívoca. Se a diferença for pequena e ambas passarem do threshold,
# consideramos marcação inválida (dupla marcação).
AMBIGUITY_MARGIN = 0.15


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


def _find_sheet_contour(gray: np.ndarray, min_area_fraction: float = 0.5) -> Optional[np.ndarray]:
    """Localiza o maior contorno quadrangular da imagem, assumido como o cartão-resposta.

    `min_area_fraction` exige que o contorno cubra uma fração mínima da imagem
    inteira — evita que uma caixa colorida interna (ex.: um cabeçalho ou tabela)
    seja confundida com a folha inteira em digitalizações sem borda impressa."""
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)

    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    img_area = gray.shape[0] * gray.shape[1]
    candidates = []
    for c in sorted(contours, key=cv2.contourArea, reverse=True)[:15]:
        area = cv2.contourArea(c)
        if area < img_area * min_area_fraction:
            continue  # muito pequeno para ser a folha inteira
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            candidates.append(approx.reshape(4, 2))

    if candidates:
        return candidates[0]

    # Fallback: se nenhum contorno de 4 vértices foi achado, usa o retângulo
    # delimitador do maior contorno (mais tolerante a folhas mal enquadradas).
    largest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest) < img_area * min_area_fraction:
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


def _bubble_ink_score(ink_map: np.ndarray, cx: int, cy: int, r: int, inner_scale: float = 0.72) -> float:
    """Calcula a intensidade média de 'tinta' (mapa contínuo, não binarizado) dentro
    de uma bolha, usando um raio um pouco menor que o círculo impresso para não
    contaminar a medida com o próprio traço impresso da bolha (o círculo em si)."""
    inner_r = max(int(r * inner_scale), 3)
    h, w = ink_map.shape
    x0, x1 = max(cx - inner_r, 0), min(cx + inner_r, w)
    y0, y1 = max(cy - inner_r, 0), min(cy + inner_r, h)
    if x1 <= x0 or y1 <= y0:
        return 0.0
    roi = ink_map[y0:y1, x0:x1]

    mask = np.zeros(roi.shape, dtype=np.uint8)
    cv2.circle(mask, (cx - x0, cy - y0), inner_r, 255, -1)

    vals = roi[mask > 0]
    if vals.size == 0:
        return 0.0
    return float(vals.mean())


def _downscale_if_large(img: np.ndarray, max_dim: int = MAX_INPUT_DIM) -> np.ndarray:
    """Reduz a imagem de entrada se ela for maior que max_dim no maior lado.
    Acelera bastante a detecção de contorno em fotos de celular de alta resolução."""
    h, w = img.shape[:2]
    largest = max(h, w)
    if largest <= max_dim:
        return img
    scale = max_dim / largest
    new_size = (int(w * scale), int(h * scale))
    return cv2.resize(img, new_size, interpolation=cv2.INTER_AREA)


def process_sheet(img: np.ndarray, template: CardTemplate) -> OMRResult:
    """Executa o pipeline completo de OMR sobre a imagem do cartão-resposta."""
    if img is None or img.size == 0:
        raise UnreadableImageError()

    img = _downscale_if_large(img)

    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    except cv2.error as e:
        raise UnreadableImageError() from e

    quad = _find_sheet_contour(gray)
    if quad is None:
        # Fallback para digitalizações (scanner): se a página não tem uma borda
        # impressa com contraste contra o fundo, não existe um contorno de "folha
        # inteira" para detectar. Nesse caso, se a proporção da imagem já bate com
        # a proporção esperada do template, assumimos que a imagem inteira já é o
        # cartão (sem necessidade de correção de perspectiva) em vez de falhar.
        img_h, img_w = gray.shape[:2]
        img_aspect = img_w / img_h
        tpl_aspect = template.canonical_width / template.canonical_height
        if abs(img_aspect - tpl_aspect) / tpl_aspect < 0.15:
            quad = np.array([[0, 0], [img_w - 1, 0], [img_w - 1, img_h - 1], [0, img_h - 1]])
        else:
            raise CardNotFoundError()

    try:
        warped = _warp_to_canonical(img, quad, template.canonical_width, template.canonical_height)
    except cv2.error as e:
        raise ProcessingError("Falha ao corrigir a perspectiva do cartão.") from e

    # ---- Mapa de "tinta" contínuo (não um único threshold binário global) ----
    # Em vez de binarizar a folha inteira com um só limiar (Otsu), o que é frágil
    # quando há blocos de fundo colorido (ex.: cabeçalhos azul-claro) e marcações
    # de caneta mais fracas, calculamos um "score de tinta" por pixel a partir do
    # espaço de cor HSV: saturação alta (tinta azul) OU baixo brilho (tinta preta)
    # contam como tinta. O papel branco tem saturação baixa e brilho alto, então
    # fica perto de zero nesse mapa.
    warped_blur = cv2.GaussianBlur(warped, (3, 3), 0)
    hsv = cv2.cvtColor(warped_blur, cv2.COLOR_BGR2HSV)
    sat = hsv[:, :, 1].astype(np.float32)
    val = hsv[:, :, 2].astype(np.float32)
    ink_map = np.clip(sat + (255.0 - val), 0, 510)

    # Referências de "papel" (bem claro) e "tinta" (bem escuro/saturado) estimadas
    # a partir da própria imagem (percentis), para se adaptar a diferentes
    # scanners/câmeras/iluminação sem depender de um limiar fixo.
    paper_ref = float(np.percentile(ink_map, 8))
    ink_ref = float(np.percentile(ink_map, 99.5))
    if ink_ref - paper_ref < 60:
        ink_ref = paper_ref + 60  # garante uma faixa mínima de contraste

    W, H = template.canonical_width, template.canonical_height
    by_question = template.regions_by_question()

    readings: List[QuestionReading] = []
    for q_num in sorted(by_question.keys()):
        bubbles_meta = by_question[q_num]
        bubble_readings: List[BubbleReading] = []
        for b in bubbles_meta:
            cx, cy = int(b.cx * W), int(b.cy * H)
            r = max(int(b.r * W), 4)
            raw_score = _bubble_ink_score(ink_map, cx, cy, r)
            ratio = float(np.clip((raw_score - paper_ref) / (ink_ref - paper_ref), 0.0, 1.0))
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
