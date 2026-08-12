import "./ProcessedImageView.css";

interface ProcessedImageViewProps {
  base64Png: string;
}

export default function ProcessedImageView({ base64Png }: ProcessedImageViewProps) {
  return (
    <div>
      <div className="legend">
        <span className="legend-item">
          <span className="legend-dot" style={{ background: "var(--ok)" }} />
          Correta
        </span>
        <span className="legend-item">
          <span className="legend-dot" style={{ background: "var(--bad)" }} />
          Errada (contorno verde = gabarito)
        </span>
        <span className="legend-item">
          <span className="legend-dot" style={{ background: "var(--warn)" }} />
          Sem resposta
        </span>
        <span className="legend-item">
          <span className="legend-dot" style={{ background: "var(--invalid)" }} />
          Marcação inválida
        </span>
      </div>
      <div className="processed-image-frame">
        <img src={`data:image/png;base64,${base64Png}`} alt="Folha processada com marcações de correção" />
      </div>
    </div>
  );
}
