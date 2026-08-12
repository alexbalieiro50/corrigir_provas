import "./ResultsTable.css";
import type { AnswerItem, QuestionStatus } from "../types";

interface ResultsTableProps {
  answers: AnswerItem[];
}

const STATUS_LABEL: Record<QuestionStatus, string> = {
  correct: "Correta",
  wrong: "Errada",
  blank: "Sem resposta",
  invalid: "Marcação inválida",
};

const STATUS_CLASS: Record<QuestionStatus, string> = {
  correct: "status-correct",
  wrong: "status-wrong",
  blank: "status-blank",
  invalid: "status-invalid",
};

export default function ResultsTable({ answers }: ResultsTableProps) {
  return (
    <div className="results-table-wrap">
      <table className="results-table">
        <thead>
          <tr>
            <th>Questão</th>
            <th>Marcada</th>
            <th>Gabarito</th>
            <th>Resultado</th>
            <th>Confiança</th>
          </tr>
        </thead>
        <tbody>
          {answers.map((a) => (
            <tr key={a.question}>
              <td className="mono">{a.question}</td>
              <td className="mono">{a.marked ?? "—"}</td>
              <td className="mono">{a.correct ?? "—"}</td>
              <td>
                <span className={`status-pill ${STATUS_CLASS[a.status]}`}>{STATUS_LABEL[a.status]}</span>
              </td>
              <td className="mono confidence-cell">{Math.round(a.confidence * 100)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
