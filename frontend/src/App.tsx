import { useState } from "react";
import Header from "./components/Header";
import FiducialCard from "./components/FiducialCard";
import AnswerKeyInput from "./components/AnswerKeyInput";
import UploadArea from "./components/UploadArea";
import ResultsSummary from "./components/ResultsSummary";
import ResultsTable from "./components/ResultsTable";
import ProcessedImageView from "./components/ProcessedImageView";
import ErrorBanner from "./components/ErrorBanner";
import TemplateSelect from "./components/TemplateSelect";
import { correctSheet } from "./services/api";
import type { CorrectionResponse, PageResult } from "./types";
import "./App.css";

type Status = "idle" | "loading" | "success" | "error";

export default function App() {
  const [answerKey, setAnswerKey] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [templateName, setTemplateName] = useState("amatura_45");
  const [candidateName, setCandidateName] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [result, setResult] = useState<CorrectionResponse | null>(null);
  const [activePage, setActivePage] = useState(0);

  const canSubmit = answerKey.trim().length > 0 && file !== null && status !== "loading";

  async function handleSubmit() {
    if (!file) return;
    setStatus("loading");
    setErrorMessage(null);
    try {
      const data = await correctSheet(file, answerKey, templateName);
      setResult(data);
      setActivePage(0);
      setStatus("success");
    } catch (err) {
      setStatus("error");
      setErrorMessage(err instanceof Error ? err.message : "Erro inesperado ao processar o cartão.");
    }
  }

  const currentPage: PageResult | null = result ? result.pages[activePage] : null;

  return (
    <div className="app-shell">
      <Header />

      <main className="app-main">
        <div className="no-print">
          <TemplateSelect value={templateName} onChange={setTemplateName} disabled={status === "loading"} />
        </div>

        <FiducialCard className="no-print">
          <AnswerKeyInput value={answerKey} onChange={setAnswerKey} disabled={status === "loading"} />
        </FiducialCard>

        <FiducialCard className="no-print">
          <UploadArea file={file} onFileSelected={setFile} disabled={status === "loading"} />
        </FiducialCard>

        <div className="submit-row no-print">
          <button className="submit-btn" onClick={handleSubmit} disabled={!canSubmit}>
            {status === "loading" ? (
              <>
                <span className="spinner" aria-hidden="true" />
                Processando cartão-resposta...
              </>
            ) : (
              "Corrigir cartão"
            )}
          </button>
          {!canSubmit && status !== "loading" && (
            <span className="submit-hint">Informe o gabarito e envie um cartão para habilitar a correção.</span>
          )}
        </div>

        {status === "error" && errorMessage && <ErrorBanner message={errorMessage} />}

        {status === "success" && result && currentPage && (
          <div className="results-section">
            {result.pages.length > 1 && (
              <div className="page-tabs no-print">
                {result.pages.map((p, i) => (
                  <button
                    key={p.page}
                    className={`page-tab ${i === activePage ? "page-tab-active" : ""}`}
                    onClick={() => setActivePage(i)}
                  >
                    Página {p.page}
                  </button>
                ))}
              </div>
            )}

            <div className="print-report">
              <div className="print-report-header">
                <div>
                  <h2 className="print-report-title">Resultado da correção</h2>
                  <label className="candidate-name-field">
                    Nome do candidato
                    <input
                      type="text"
                      value={candidateName}
                      onChange={(e) => setCandidateName(e.target.value)}
                      placeholder="(opcional) digite o nome para exibir na impressão"
                    />
                  </label>
                </div>
                <button className="print-btn no-print" onClick={() => window.print()}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <path
                      d="M6 9V4h12v5M6 18h12v3H6v-3zM6 14h12M4 9h16a1 1 0 011 1v5a1 1 0 01-1 1h-3M4 9a1 1 0 00-1 1v5a1 1 0 001 1h3"
                      stroke="currentColor"
                      strokeWidth="1.6"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                  Imprimir resultado
                </button>
              </div>

              <FiducialCard>
                <h2 className="section-label">03 — Resultado</h2>
                <div className="results-body">
                  <ResultsSummary result={currentPage} />
                </div>
              </FiducialCard>

              <FiducialCard>
                <h2 className="section-label" style={{ marginBottom: 14 }}>
                  Detalhamento por questão
                </h2>
                <ResultsTable answers={currentPage.answers} />
              </FiducialCard>

              {currentPage.processedImageBase64 && (
                <FiducialCard className="no-print">
                  <h2 className="section-label" style={{ marginBottom: 14 }}>
                    Folha processada
                  </h2>
                  <ProcessedImageView base64Png={currentPage.processedImageBase64} />
                </FiducialCard>
              )}
            </div>
          </div>
        )}
      </main>

      <footer className="app-footer no-print">
        <p>Desenvolvido por <b>Alex Balieiro</b></p>
        <p>v1.0.0 (MVP)</p>
      </footer>
    </div>
  );
}
