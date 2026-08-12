"""
Define o modelo (template) de cartão-resposta suportado pelo MVP.
"""

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class BubbleRegion:
    """Região (em coordenadas normalizadas 0..1 da folha já corrigida em perspectiva)
    correspondente a UMA bolha (uma alternativa de uma questão)."""
    question: int
    alternative: str
    cx: float  # centro X normalizado (0..1)
    cy: float  # centro Y normalizado (0..1)
    r: float   # raio normalizado (relativo à largura da folha)


@dataclass
class CardTemplate:
    name: str
    question_count: int
    alternatives: List[str]
    canonical_width: int = 1000
    canonical_height: int = 1400
    columns: int = 3
    rows_per_column: int = 15
    
    # --- CORREÇÃO DE ALTURA (Y) E LARGURA (X) ---
    grid_top: float = 0.548       # Valor bem menor para SUBIR a linha 01 até a posição correta
    grid_bottom: float = 0.920    # Reduzido para encerrar na linha 15 (acima do rodapé)
    grid_left: float = 0.023     # Recuado levemente para alinhar a 1ª coluna
    grid_right: float = 0.960     # Expandido levemente para cobrir a coluna D da 3ª tabela
    column_gap: float = 0.048     # Espaçamento entre as 3 colunas principais
    bubble_radius: float = 0.015  # Tamanho visual da bolha

    answer_regions: List[BubbleRegion] = field(default_factory=list, init=False)

    def __post_init__(self):
        self.answer_regions = self._build_regions()

    def _build_regions(self) -> List[BubbleRegion]:
        regions: List[BubbleRegion] = []
        n_alt = len(self.alternatives)

        total_questions = self.question_count
        q_per_col = self.rows_per_column
        n_cols = self.columns
        assert q_per_col * n_cols >= total_questions, (
            "columns * rows_per_column deve ser >= question_count"
        )

        usable_width = self.grid_right - self.grid_left
        col_width = (usable_width - self.column_gap * (n_cols - 1)) / n_cols

        usable_height = self.grid_bottom - self.grid_top
        row_height = usable_height / q_per_col

        # Largura da coluna com o número da questão ("01", "02", etc.)
        label_width = col_width * 0.26
        alts_width = col_width - label_width
        alt_spacing = alts_width / n_alt

        q_num = 1
        for col in range(n_cols):
            col_x0 = self.grid_left + col * (col_width + self.column_gap)
            for row in range(q_per_col):
                if q_num > total_questions:
                    break
                cy = self.grid_top + row * row_height + row_height / 2
                for i, alt in enumerate(self.alternatives):
                    cx = col_x0 + label_width + alt_spacing * i + alt_spacing / 2
                    regions.append(
                        BubbleRegion(
                            question=q_num,
                            alternative=alt,
                            cx=cx,
                            cy=cy,
                            r=self.bubble_radius,
                        )
                    )
                q_num += 1

        return regions

    def regions_by_question(self) -> Dict[int, List[BubbleRegion]]:
        out: Dict[int, List[BubbleRegion]] = {}
        for r in self.answer_regions:
            out.setdefault(r.question, []).append(r)
        return out


DEFAULT_TEMPLATE = CardTemplate(
    name="default_45",
    question_count=45,
    alternatives=["A", "B", "C", "D"],
    columns=3,
    rows_per_column=15,
)

TEMPLATES: Dict[str, CardTemplate] = {
    DEFAULT_TEMPLATE.name: DEFAULT_TEMPLATE,
    "default_40": DEFAULT_TEMPLATE,
}


def get_template(name: str = "default_45") -> CardTemplate:
    if name not in TEMPLATES:
        raise ValueError(f"Template '{name}' não encontrado.")
    return TEMPLATES[name]