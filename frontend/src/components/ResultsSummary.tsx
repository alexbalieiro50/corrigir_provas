import "./ResultsSummary.css";
import type { PageResult } from "../types";

interface ResultsSummaryProps {
  result: PageResult;
}

export default function ResultsSummary({ result }: ResultsSummaryProps) {
  const { correct, wrong, blank, invalid, score, totalQuestions } = result;

  return (
    <div className="results-summary">
      <div className="score-hero">
        <span className="score-hero-value mono">{score.toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%</span>
        <span className="score-hero-label">Aproveitamento · {totalQuestions} questões</span>
      </div>

      <div className="stat-grid">
        <div className="stat-card stat-ok">
          <span className="stat-value mono">{correct}</span>
          <span className="stat-label">Acertos</span>
        </div>
        <div className="stat-card stat-bad">
          <span className="stat-value mono">{wrong}</span>
          <span className="stat-label">Erros</span>
        </div>
        <div className="stat-card stat-warn">
          <span className="stat-value mono">{blank}</span>
          <span className="stat-label">Sem resposta</span>
        </div>
        <div className="stat-card stat-invalid">
          <span className="stat-value mono">{invalid}</span>
          <span className="stat-label">Marcação inválida</span>
        </div>
      </div>
    </div>
  );
}
