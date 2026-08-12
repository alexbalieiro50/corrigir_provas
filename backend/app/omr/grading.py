"""Compara as respostas identificadas pelo OMR com o gabarito e calcula o resultado."""

from dataclasses import dataclass
from typing import Dict, List, Optional

from .processor import QuestionReading
from .exceptions import QuestionCountMismatchError


@dataclass
class QuestionResult:
    question: int
    marked: Optional[str]
    correct_answer: Optional[str]
    status: str  # "correct" | "wrong" | "blank" | "invalid"
    confidence: float


@dataclass
class GradingSummary:
    total_questions: int
    correct: int
    wrong: int
    blank: int
    invalid: int
    score: float
    results: List[QuestionResult]


def _confidence_for(reading: QuestionReading) -> float:
    """Confiança = fração de preenchimento da bolha marcada (0 se em branco)."""
    if reading.marked is None:
        if reading.bubbles:
            return round(max(b.fill_ratio for b in reading.bubbles), 3)
        return 0.0
    for b in reading.bubbles:
        if b.alternative == reading.marked:
            return round(b.fill_ratio, 3)
    return 0.0


def grade(readings: List[QuestionReading], answer_key: Dict[int, str]) -> GradingSummary:
    if not answer_key:
        raise QuestionCountMismatchError("Gabarito vazio.")

    # Aceita gabarito com quantidade de questões diferente do template, desde que
    # os números de questão presentes no gabarito existam nas leituras do template.
    max_key_question = max(answer_key.keys())
    max_reading_question = max((r.question for r in readings), default=0)
    if max_key_question > max_reading_question:
        raise QuestionCountMismatchError(
            f"O gabarito informa {max_key_question} questões, mas o template do "
            f"cartão só possui {max_reading_question} questões."
        )

    readings_by_q = {r.question: r for r in readings}

    results: List[QuestionResult] = []
    correct = wrong = blank = invalid = 0

    for q_num in sorted(answer_key.keys()):
        expected = answer_key[q_num]
        reading = readings_by_q.get(q_num)

        if reading is None:
            # Questão do gabarito não existe na leitura (não deveria acontecer após
            # a validação acima, mas tratamos defensivamente)
            results.append(QuestionResult(q_num, None, expected, "blank", 0.0))
            blank += 1
            continue

        confidence = _confidence_for(reading)

        if reading.status == "invalid":
            status = "invalid"
            invalid += 1
        elif reading.status == "blank":
            status = "blank"
            blank += 1
        elif reading.marked == expected:
            status = "correct"
            correct += 1
        else:
            status = "wrong"
            wrong += 1

        results.append(
            QuestionResult(
                question=q_num,
                marked=reading.marked,
                correct_answer=expected,
                status=status,
                confidence=confidence,
            )
        )

    total = len(answer_key)
    score = round((correct / total) * 100, 2) if total else 0.0

    return GradingSummary(
        total_questions=total,
        correct=correct,
        wrong=wrong,
        blank=blank,
        invalid=invalid,
        score=score,
        results=results,
    )
