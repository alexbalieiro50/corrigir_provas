"""
Gera uma folha de resposta sintética (imagem) compatível com o template padrão,
para servir como dado de teste do pipeline de OMR.

Uso:
    python -m app.omr.testdata.generate_sample

Gera:
    sample_sheet.png       -> folha com algumas respostas marcadas (com leve rotação
                               e borda, para exercitar detecção de contorno + perspectiva)
    sample_answer_key.txt  -> gabarito de exemplo compatível
"""

import os
import random

import cv2
import numpy as np

from app.omr.template import DEFAULT_TEMPLATE


def _fill_bubble(img, cx, cy, r, coverage=0.85):
    """Desenha uma marcação de bolha (círculo preenchido, imitando caneta/lápis)."""
    cv2.circle(img, (cx, cy), int(r * coverage), (30, 30, 30), thickness=-1, lineType=cv2.LINE_AA)


def generate_sheet(answers: dict, out_path: str, add_perspective_noise=True):
    """`answers`: dict question -> alternativa (str) OU lista de alternativas
    (lista com 2+ itens gera marcação dupla/inválida proposital)."""
    template = DEFAULT_TEMPLATE
    W, H = template.canonical_width, template.canonical_height

    # canvas branco (folha)
    sheet = np.full((H, W, 3), 255, dtype=np.uint8)

    # cabeçalho simples
    cv2.putText(sheet, "CARTAO-RESPOSTA - TESTE", (int(W * 0.07), int(H * 0.06)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2, cv2.LINE_AA)
    cv2.putText(sheet, "Nome: ______________________________", (int(W * 0.07), int(H * 0.11)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1, cv2.LINE_AA)

    by_q = template.regions_by_question()
    for q_num, bubbles in by_q.items():
        # número da questão
        first = bubbles[0]
        label_x = int((template.grid_left) * W)
        label_y = int(first.cy * H) + 5
        cv2.putText(sheet, f"{q_num:02d}", (label_x, label_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1, cv2.LINE_AA)

        for b in bubbles:
            cx, cy, r = int(b.cx * W), int(b.cy * H), max(int(b.r * W), 4)
            cv2.circle(sheet, (cx, cy), r, (0, 0, 0), thickness=1, lineType=cv2.LINE_AA)
            cv2.putText(sheet, b.alternative, (cx - 4, cy - r - 3),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.32, (0, 0, 0), 1, cv2.LINE_AA)

        marked = answers.get(q_num)
        if marked:
            marked_alts = [marked] if isinstance(marked, str) else list(marked)
            for b in bubbles:
                if b.alternative in marked_alts:
                    cx, cy, r = int(b.cx * W), int(b.cy * H), max(int(b.r * W), 4)
                    _fill_bubble(sheet, cx, cy, r)

    # borda preta bem próxima da borda real da folha (mantém o tamanho 1000x1400,
    # para que o retângulo detectado coincida com a área normalizada do template)
    margin = 6
    cv2.rectangle(
        sheet, (margin, margin), (W - margin, H - margin), (0, 0, 0), thickness=3
    )

    final = sheet
    if add_perspective_noise:
        # aplica uma leve transformação de perspectiva para simular uma foto real
        h, w = final.shape[:2]
        src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
        jitter = 0.012
        dst = np.float32(
            [
                [random.uniform(0, jitter) * w, random.uniform(0, jitter) * h],
                [w - random.uniform(0, jitter) * w, random.uniform(0, jitter) * h],
                [w - random.uniform(0, jitter) * w, h - random.uniform(0, jitter) * h],
                [random.uniform(0, jitter) * w, h - random.uniform(0, jitter) * h],
            ]
        )
        M = cv2.getPerspectiveTransform(src, dst)
        final = cv2.warpPerspective(final, M, (w, h), borderValue=(255, 255, 255))

    # canvas maior simulando "foto" com fundo/mesa ao redor da folha
    pad = 80
    canvas = np.full((final.shape[0] + pad * 2, final.shape[1] + pad * 2, 3), (210, 210, 205), dtype=np.uint8)
    canvas[pad:pad + final.shape[0], pad:pad + final.shape[1]] = final

    cv2.imwrite(out_path, canvas)
    return out_path


def main():
    random.seed(42)
    template = DEFAULT_TEMPLATE
    total = template.question_count
    alts = template.alternatives

    # gera um gabarito aleatório "verdadeiro"
    answer_key = {q: random.choice(alts) for q in range(1, total + 1)}

    # gera as respostas do candidato: a maioria igual ao gabarito (acerto),
    # algumas erradas, uma em branco e uma marcação dupla (inválida)
    candidate_answers = dict(answer_key)
    wrong_questions = random.sample(range(1, total + 1), 5)
    for q in wrong_questions[:3]:
        wrong_alt = random.choice([a for a in alts if a != answer_key[q]])
        candidate_answers[q] = wrong_alt
    blank_q = wrong_questions[3]
    del candidate_answers[blank_q]
    invalid_q = wrong_questions[4]
    other_alt = random.choice([a for a in alts if a != answer_key[invalid_q]])
    candidate_answers[invalid_q] = [answer_key[invalid_q], other_alt]  # marcação dupla

    here = os.path.dirname(os.path.abspath(__file__))
    sheet_path = os.path.join(here, "sample_sheet.png")
    key_path = os.path.join(here, "sample_answer_key.txt")

    generate_sheet(candidate_answers, sheet_path)

    with open(key_path, "w", encoding="utf-8") as f:
        for q in range(1, total + 1):
            f.write(f"{q}-{answer_key[q]}\n")

    print(f"Folha de teste gerada em: {sheet_path}")
    print(f"Gabarito de teste gerado em: {key_path}")
    print(f"Questão em branco (proposital): {blank_q}")
    print(f"Questão com marcação dupla/inválida (proposital): {invalid_q}")
    print(f"Questões erradas (proposital): {wrong_questions[:3]}")


if __name__ == "__main__":
    main()
