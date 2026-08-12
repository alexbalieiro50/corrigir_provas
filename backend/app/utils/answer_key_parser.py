"""Interpreta o gabarito informado pelo usuário em formato texto.

Formatos aceitos (uma questão por linha, ou separadas por vírgula/quebra de linha):
  1-A
  1:A
  1 A
  1) A
"""

import re
from typing import Dict

from ..omr.exceptions import InvalidAnswerKeyError

_LINE_RE = re.compile(r"^\s*(\d+)\s*[-:\).]?\s*([A-Za-z])\s*$")


def parse_answer_key(raw_text: str) -> Dict[int, str]:
    if not raw_text or not raw_text.strip():
        raise InvalidAnswerKeyError("Gabarito vazio. Informe pelo menos uma questão.")

    answer_key: Dict[int, str] = {}
    # aceita separação por vírgula ou quebras de linha
    tokens = re.split(r"[,\n]+", raw_text.strip())

    for token in tokens:
        token = token.strip()
        if not token:
            continue
        match = _LINE_RE.match(token)
        if not match:
            raise InvalidAnswerKeyError(
                f"Formato de gabarito inválido em: '{token}'. Use o formato '1-A' ou '1:A'."
            )
        q_num = int(match.group(1))
        alt = match.group(2).upper()
        answer_key[q_num] = alt

    if not answer_key:
        raise InvalidAnswerKeyError("Não foi possível interpretar nenhuma questão do gabarito.")

    return answer_key
