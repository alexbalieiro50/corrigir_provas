import "./AnswerKeyInput.css";

interface AnswerKeyInputProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

const PLACEHOLDER = `1:A
2:C
3:B
4:D
5:A
6:B
7:C
8:D
9:A
10:C`;

function countParsedQuestions(text: string): number {
  const lineRe = /^\s*(\d+)\s*[-:).]?\s*([A-Za-z])\s*$/;
  const tokens = text.split(/[,\n]+/);
  let count = 0;
  for (const t of tokens) {
    if (t.trim() && lineRe.test(t.trim())) count++;
  }
  return count;
}

export default function AnswerKeyInput({ value, onChange, disabled }: AnswerKeyInputProps) {
  const parsedCount = countParsedQuestions(value);

  return (
    <section>
      <div className="section-label-row">
        <h2 className="section-label">01 — Gabarito</h2>
        {value.trim() && (
          <span className="parsed-badge mono">
            {parsedCount} {parsedCount === 1 ? "questão reconhecida" : "questões reconhecidas"}
          </span>
        )}
      </div>
      <p className="section-hint">
        Cole o gabarito, uma questão por linha. Aceita os formatos <code>1-A</code>, <code>1:A</code> ou{" "}
        <code>1) A</code>.
      </p>
      <textarea
        className="answer-key-textarea mono"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={PLACEHOLDER}
        rows={8}
        disabled={disabled}
        spellCheck={false}
      />
    </section>
  );
}
