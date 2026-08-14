import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import type { PageResult, QuestionStatus } from "../types";

interface ReportOptions {
  candidateName: string;
  templateLabel: string;
}

const STATUS_LABEL: Record<QuestionStatus, string> = {
  correct: "Correta",
  wrong: "Errada",
  blank: "Sem resposta",
  invalid: "Inválida",
};

// Cores (RGB) usadas na tabela — mesma paleta da interface e da imagem processada
const STATUS_COLOR: Record<QuestionStatus, [number, number, number]> = {
  correct: [31, 157, 85],
  wrong: [214, 48, 74],
  blank: [201, 130, 15],
  invalid: [139, 63, 209],
};

function sanitizeFilename(name: string): string {
  return name
    .trim()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^\w\-]+/g, "_")
    .replace(/_+/g, "_")
    .replace(/^_|_$/g, "");
}

/**
 * Gera e baixa um PDF com o resultado da correção: cabeçalho (candidato/data/
 * modelo do cartão), resumo (aproveitamento e estatísticas), tabela detalhada
 * por questão e, em uma segunda página, a folha processada com as marcações
 * coloridas (acertos/erros/em branco/inválidas).
 */
export function downloadCorrectionPdf(result: PageResult, options: ReportOptions) {
  const doc = new jsPDF({ unit: "pt", format: "a4" });
  const pageWidth = doc.internal.pageSize.getWidth();
  const margin = 40;
  let y = 50;

  doc.setFont("helvetica", "bold");
  doc.setFontSize(18);
  doc.text("Resultado da correção", margin, y);
  y += 22;

  doc.setDrawColor(210, 210, 210);
  doc.line(margin, y, pageWidth - margin, y);
  y += 22;

  doc.setFont("helvetica", "normal");
  doc.setFontSize(11);
  doc.setTextColor(60, 60, 60);

  const dateStr = new Date().toLocaleString("pt-BR");
  if (options.candidateName.trim()) {
    doc.setFont("helvetica", "bold");
    doc.text("Candidato:", margin, y);
    doc.setFont("helvetica", "normal");
    doc.text(options.candidateName.trim(), margin + 68, y);
    y += 16;
  }
  doc.setFont("helvetica", "bold");
  doc.text("Modelo do cartão:", margin, y);
  doc.setFont("helvetica", "normal");
  doc.text(options.templateLabel, margin + 110, y);
  y += 16;
  doc.setFont("helvetica", "bold");
  doc.text("Gerado em:", margin, y);
  doc.setFont("helvetica", "normal");
  doc.text(dateStr, margin + 70, y);
  y += 30;

  // ---- Resumo ----
  doc.setFillColor(20, 22, 28);
  doc.roundedRect(margin, y, pageWidth - margin * 2, 46, 4, 4, "F");
  doc.setTextColor(0, 194, 168);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(22);
  doc.text(`${result.score.toFixed(1)}%`, margin + 14, y + 30);

  doc.setTextColor(230, 230, 230);
  doc.setFontSize(10);
  doc.setFont("helvetica", "normal");
  doc.text(`Aproveitamento · ${result.totalQuestions} questões`, margin + 120, y + 28);
  y += 62;

  doc.setTextColor(30, 30, 30);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(11);
  const statsLine = [
    `Acertos: ${result.correct}`,
    `Erros: ${result.wrong}`,
    `Sem resposta: ${result.blank}`,
    `Marcação inválida: ${result.invalid}`,
  ].join("      ");
  doc.text(statsLine, margin, y);
  y += 24;

  // ---- Tabela detalhada ----
  autoTable(doc, {
    startY: y,
    head: [["Questão", "Marcada", "Gabarito", "Resultado"]],
    body: result.answers.map((a) => [
      String(a.question),
      a.marked ?? "—",
      a.correct ?? "—",
      STATUS_LABEL[a.status],
    ]),
    styles: { fontSize: 9, cellPadding: 5, textColor: [30, 30, 30] },
    headStyles: { fillColor: [20, 22, 28], textColor: [245, 243, 236], fontStyle: "bold" },
    alternateRowStyles: { fillColor: [248, 247, 242] },
    margin: { left: margin, right: margin },
    didParseCell: (data: any) => {
      if (data.section === "body" && data.column.index === 3) {
        const status = result.answers[data.row.index].status as QuestionStatus;
        const color = STATUS_COLOR[status];
        if (color) {
          data.cell.styles.textColor = color;
          data.cell.styles.fontStyle = "bold";
        }
      }
    },
  });

  // ---- Folha processada (nova página) ----
  if (result.processedImageBase64) {
    doc.addPage();
    doc.setTextColor(20, 20, 20);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(13);
    doc.text("Folha processada", margin, 44);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(9);
    doc.setTextColor(100, 100, 100);
    doc.text(
      "Verde = correta · Vermelho = errada (contorno verde indica o gabarito) · Laranja = sem resposta · Roxo = inválida",
      margin,
      60
    );

    const imgData = `data:image/jpeg;base64,${result.processedImageBase64}`;
    const imgProps = doc.getImageProperties(imgData);
    const ratio = imgProps.height / imgProps.width;
    const maxWidth = pageWidth - margin * 2;
    const pageHeight = doc.internal.pageSize.getHeight();
    const availableHeight = pageHeight - 90 - margin;

    let drawWidth = maxWidth;
    let drawHeight = drawWidth * ratio;
    if (drawHeight > availableHeight) {
      drawHeight = availableHeight;
      drawWidth = drawHeight / ratio;
    }
    const x = margin + (maxWidth - drawWidth) / 2;
    doc.addImage(imgData, "JPEG", x, 78, drawWidth, drawHeight);
  }

  const base = options.candidateName.trim() ? sanitizeFilename(options.candidateName) : "cartao";
  doc.save(`resultado-${base || "cartao"}.pdf`);
}
