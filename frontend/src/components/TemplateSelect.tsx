import "./TemplateSelect.css";

export interface TemplateOption {
  value: string;
  label: string;
}

export const TEMPLATE_OPTIONS: TemplateOption[] = [
  { value: "amatura_45", label: "Amaturá — 45 questões (A–D)" },
  { value: "default_40", label: "Padrão MVP — 40 questões (A–E)" },
];

export function getTemplateLabel(value: string): string {
  return TEMPLATE_OPTIONS.find((opt) => opt.value === value)?.label ?? value;
}

interface TemplateSelectProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export default function TemplateSelect({ value, onChange, disabled }: TemplateSelectProps) {
  return (
    <div className="template-select-row">
      <label htmlFor="template-select" className="template-select-label">
        Modelo do cartão
      </label>
      <select
        id="template-select"
        className="template-select"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
      >
        {TEMPLATE_OPTIONS.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}
