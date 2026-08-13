"""
Define o modelo (template) de cartão-resposta suportado pelo MVP.

Para o MVP, usamos um único template conhecido, com layout em grade (colunas x linhas).
A estrutura foi pensada para permitir, no futuro, múltiplos templates (P2), bastando
criar novas instâncias de CardTemplate e registrá-las em TEMPLATES.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


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
    # Dimensões canônicas (em pixels) para as quais a imagem é "esticada" (warp)
    canonical_width: int = 1000
    canonical_height: int = 1400
    # Parâmetros de layout em grade (colunas de questões) — usados apenas quando
    # `explicit_regions` não é informado (geração automática/formulaica da grade).
    columns: int = 4
    rows_per_column: int = 10
    grid_top: float = 0.20       # início da grade (fração da altura)
    grid_bottom: float = 0.95    # fim da grade (fração da altura)
    grid_left: float = 0.07      # início da grade (fração da largura)
    grid_right: float = 0.97     # fim da grade (fração da largura)
    column_gap: float = 0.02     # espaço extra entre colunas (fração da largura)
    bubble_radius: float = 0.012  # raio da bolha (fração da largura)
    # Regiões medidas manualmente/precisamente (bypassa a geração formulaica acima).
    # Use isso para cartões reais calibrados a partir de coordenadas de pixel exatas.
    explicit_regions: Optional[List[BubbleRegion]] = field(default=None, repr=False)

    answer_regions: List[BubbleRegion] = field(default_factory=list, init=False)

    def __post_init__(self):
        if self.explicit_regions is not None:
            self.answer_regions = self.explicit_regions
        else:
            self.answer_regions = self._build_regions()

    def _build_regions(self) -> List[BubbleRegion]:
        """Gera as posições das bolhas programaticamente a partir dos parâmetros de grade.

        Isso evita hard-code de cada bolha individualmente, mas ainda assim usa
        coordenadas conhecidas/fixas em relação à folha corrigida, o que é aceitável
        para o MVP (seção 6 dos requisitos).
        """
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

        # Dentro de cada coluna: um pequeno espaço para o número da questão,
        # depois as bolhas das alternativas distribuídas uniformemente.
        label_width = col_width * 0.18
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


# Template padrão do MVP: 40 questões, alternativas A-E, layout em 4 colunas x 10 linhas.
DEFAULT_TEMPLATE = CardTemplate(
    name="default_40",
    question_count=40,
    alternatives=["A", "B", "C", "D", "E"],
    columns=4,
    rows_per_column=10,
)


def _build_amatura_45_regions() -> List[BubbleRegion]:
    """Regiões medidas diretamente em pixels a partir de um cartão real (escaneado
    em Epson L3250, 300 DPI, 2480x3505px) da Prefeitura de Amaturá: 45 questões,
    alternativas A-D, em 3 blocos de 15 questões (1-15, 16-30, 31-45).

    Coordenadas de coluna obtidas por detecção automática de círculos (Hough
    Circle Transform) sobre o PDF do cartão em branco/preenchido, agrupadas por
    proximidade. Ver backend/app/omr/testdata/calibrate_grid.py para reproduzir
    ou recalibrar caso o layout do cartão mude.
    """
    SCAN_W, SCAN_H = 2480, 3505

    # Centro X (em px, na resolução de escaneamento acima) de cada uma das 12
    # colunas de bolhas: 3 blocos x 4 alternativas (A, B, C, D).
    col_x_px = [
        302.7, 431.7, 562.3, 691.5,     # bloco 1 (questões 1-15)
        1098.1, 1228.0, 1357.2, 1487.1,  # bloco 2 (questões 16-30)
        1891.0, 2020.2, 2149.8, 2279.3,  # bloco 3 (questões 31-45)
    ]
    row0_y_px = 1947.5   # centro Y da primeira linha (questões 01/16/31)
    row_step_px = 84.357  # espaçamento vertical entre linhas consecutivas
    n_rows = 15
    alternatives = ["A", "B", "C", "D"]
    bubble_r_px = 20.0  # raio usado para a máscara de leitura (cobre a bolha impressa)

    regions: List[BubbleRegion] = []
    for block in range(3):
        for row in range(n_rows):
            question = block * n_rows + row + 1
            cy = (row0_y_px + row * row_step_px) / SCAN_H
            for alt_idx, alt in enumerate(alternatives):
                cx = col_x_px[block * 4 + alt_idx] / SCAN_W
                regions.append(
                    BubbleRegion(question=question, alternative=alt, cx=cx, cy=cy, r=bubble_r_px / SCAN_W)
                )
    return regions


AMATURA_45_TEMPLATE = CardTemplate(
    name="amatura_45",
    question_count=45,
    alternatives=["A", "B", "C", "D"],
    canonical_width=2480,
    canonical_height=3505,
    explicit_regions=_build_amatura_45_regions(),
)

TEMPLATES: Dict[str, CardTemplate] = {
    DEFAULT_TEMPLATE.name: DEFAULT_TEMPLATE,
    AMATURA_45_TEMPLATE.name: AMATURA_45_TEMPLATE,
}


def get_template(name: str = "default_40") -> CardTemplate:
    if name not in TEMPLATES:
        raise ValueError(f"Template '{name}' não encontrado.")
    return TEMPLATES[name]
