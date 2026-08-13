"""Gera uma imagem de visualização da folha processada, marcando as bolhas
analisadas e destacando o resultado (correta/errada/em branco/inválida)."""

from typing import Dict, List

import cv2  # type: ignore
import numpy as np  # type: ignore[import-not-found]

from .processor import QuestionReading
from .grading import QuestionResult

COLOR_CORRECT = (0, 170, 0)      # verde
COLOR_WRONG = (0, 0, 220)        # vermelho
COLOR_BLANK = (0, 165, 255)      # laranja
COLOR_INVALID = (200, 0, 200)    # roxo
COLOR_UNANALYZED = (180, 180, 180)  # cinza (bolha não marcada, apenas contorno)

STATUS_COLOR = {
    "correct": COLOR_CORRECT,
    "wrong": COLOR_WRONG,
    "blank": COLOR_BLANK,
    "invalid": COLOR_INVALID,
}


def render_result_image(
    warped_image: np.ndarray,
    readings: List[QuestionReading],
    results: List[QuestionResult],
) -> np.ndarray:
    out = warped_image.copy()
    results_by_q: Dict[int, QuestionResult] = {r.question: r for r in results}

    for reading in readings:
        result = results_by_q.get(reading.question)
        status_color = STATUS_COLOR.get(result.status, COLOR_UNANALYZED) if result else COLOR_UNANALYZED

        for bubble in reading.bubbles:
            cx, cy = bubble.center_px
            r = bubble.radius_px
            is_marked = reading.marked == bubble.alternative

            if is_marked:
                cv2.circle(out, (cx, cy), r + 2, status_color, thickness=2)
                cv2.circle(out, (cx, cy), max(r - 2, 1), status_color, thickness=-1)
            else:
                # bolha analisada mas não marcada: apenas um contorno leve
                cv2.circle(out, (cx, cy), r, COLOR_UNANALYZED, thickness=1)

        # se a questão está errada, também destaca (com um "x" leve) a bolha do gabarito
        if result and result.status == "wrong" and result.correct_answer:
            for bubble in reading.bubbles:
                if bubble.alternative == result.correct_answer:
                    cx, cy = bubble.center_px
                    r = bubble.radius_px
                    cv2.circle(out, (cx, cy), r + 4, COLOR_CORRECT, thickness=2)

    return out


def encode_png(img: np.ndarray) -> bytes:
    ok, buf = cv2.imencode(".png", img)
    if not ok:
        raise RuntimeError("Falha ao codificar imagem de resultado.")
    return buf.tobytes()
