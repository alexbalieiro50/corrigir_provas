import { useState } from "react";
import Header from "./components/Header";
import FiducialCard from "./components/FiducialCard";
import AnswerKeyInput from "./components/AnswerKeyInput";
import UploadArea from "./components/UploadArea";
import ResultsSummary from "./components/ResultsSummary";
import ResultsTable from "./components/ResultsTable";
import ProcessedImageView from "./components/ProcessedImageView";
import ErrorBanner from "./components/ErrorBanner";
import { correctSheet } from "./services/api";
import type { CorrectionResponse, PageResult } from "./types";
import "./App.css";

type Status = "idle" | "loading" | "success" | "error";

export default function App() {
  const [answerKey, setAnswerKey] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<Status>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [result, setResult] = useState<CorrectionResponse | null>(null);
  const [activePage, setActivePage] = useState(0);

  const canSubmit =
    answerKey.trim().length > 0 && file !== null && status !== "loading";

  async function handleSubmit() {
    if (!file) return;
    setStatus("loading");
    setErrorMessage(null);
    try {
      const data = await correctSheet(file, answerKey);
      setResult(data);
      setActivePage(0);
      setStatus("success");
    } catch (err) {
      setStatus("error");
      setErrorMessage(
        err instanceof Error
          ? err.message
          : "Erro inesperado ao processar o cartão.",
      );
    }
  }

  const currentPage: PageResult | null = result
    ? result.pages[activePage]
    : null;

  return (
    <div className="app-shell">
      <Header />

      <main className="app-main">
        <FiducialCard>
          <AnswerKeyInput
            value={answerKey}
            onChange={setAnswerKey}
            disabled={status === "loading"}
          />
        </FiducialCard>

        <FiducialCard>
          <UploadArea
            file={file}
            onFileSelected={setFile}
            disabled={status === "loading"}
          />
        </FiducialCard>

        <div className="submit-row">
          <button
            className="submit-btn"
            onClick={handleSubmit}
            disabled={!canSubmit}
          >
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
            <span className="submit-hint">
              Informe o gabarito e envie um cartão para habilitar a correção.
            </span>
          )}
        </div>

        {status === "error" && errorMessage && (
          <ErrorBanner message={errorMessage} />
        )}

        {status === "success" && result && currentPage && (
          <div className="results-section">
            {result.pages.length > 1 && (
              <div className="page-tabs">
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
              <FiducialCard>
                <h2 className="section-label" style={{ marginBottom: 14 }}>
                  Folha processada
                </h2>
                <ProcessedImageView
                  base64Png={currentPage.processedImageBase64}
                />
              </FiducialCard>
            )}
          </div>
        )}
      </main>

      <footer className="app-footer">
        <span>R. Frei Pio, Nº 295 – Centro – Cep: 69620-00</span>
        <br />
        <span>Tel. (97) 3463-1259 – Amaturá -Am</span>
      </footer>
    </div>
  );
}
