import { useRef, useState, type DragEvent } from "react";
import CameraCapture from "./CameraCapture";
import "./UploadArea.css";

interface UploadAreaProps {
  file: File | null;
  onFileSelected: (file: File | null) => void;
  disabled?: boolean;
}

const ACCEPTED_EXTENSIONS = ["jpg", "jpeg", "png", "pdf"];
const ACCEPTED_MIME = ["image/jpeg", "image/png", "application/pdf"];

function isAccepted(file: File): boolean {
  const ext = file.name.split(".").pop()?.toLowerCase() ?? "";
  return ACCEPTED_EXTENSIONS.includes(ext) || ACCEPTED_MIME.includes(file.type);
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function UploadArea({ file, onFileSelected, disabled }: UploadAreaProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [rejectionMessage, setRejectionMessage] = useState<string | null>(null);
  const [showCamera, setShowCamera] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function handleFiles(fileList: FileList | null) {
    if (!fileList || fileList.length === 0) return;
    const candidate = fileList[0];
    if (!isAccepted(candidate)) {
      setRejectionMessage("Formato não suportado. Envie um arquivo JPG, JPEG, PNG ou PDF.");
      return;
    }
    setRejectionMessage(null);
    onFileSelected(candidate);
  }

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setIsDragOver(false);
    if (disabled) return;
    handleFiles(e.dataTransfer.files);
  }

  return (
    <section>
      <h2 className="section-label">02 — Cartão-resposta</h2>
      <p className="section-hint">Envie o cartão-resposta preenchido para leitura.</p>

      <div
        className={`upload-drop ${isDragOver ? "upload-drop-active" : ""} ${file ? "upload-drop-has-file" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setIsDragOver(true);
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        onClick={() => !disabled && inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if ((e.key === "Enter" || e.key === " ") && !disabled) inputRef.current?.click();
        }}
        aria-disabled={disabled}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".jpg,.jpeg,.png,.pdf,image/jpeg,image/png,application/pdf"
          hidden
          disabled={disabled}
          onChange={(e) => handleFiles(e.target.files)}
        />

        {!file && (
          <>
            <div className="upload-icon" aria-hidden="true">
              <svg width="30" height="30" viewBox="0 0 24 24" fill="none">
                <path
                  d="M12 16V4M12 4L7 9M12 4l5 5"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                <path
                  d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
            <p className="upload-title">Envie o cartão-resposta</p>
            <p className="upload-subtitle">Arraste e solte, ou clique para selecionar — JPG, JPEG, PNG ou PDF</p>
            <button
              type="button"
              className="camera-trigger-btn"
              onClick={(e) => {
                e.stopPropagation();
                if (!disabled) setShowCamera(true);
              }}
              disabled={disabled}
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path
                  d="M4 8a2 2 0 012-2h1.5l1-1.5h7l1 1.5H18a2 2 0 012 2v9a2 2 0 01-2 2H6a2 2 0 01-2-2V8z"
                  stroke="currentColor"
                  strokeWidth="1.6"
                  strokeLinejoin="round"
                />
                <circle cx="12" cy="13" r="3.2" stroke="currentColor" strokeWidth="1.6" />
              </svg>
              Usar câmera
            </button>
          </>
        )}

        {file && (
          <div className="upload-file-info">
            <div className="upload-file-icon" aria-hidden="true">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                <path
                  d="M9 12l2 2 4-4"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                <circle cx="12" cy="12" r="9.5" stroke="currentColor" strokeWidth="1.5" />
              </svg>
            </div>
            <div>
              <p className="upload-filename">{file.name}</p>
              <p className="upload-filesize mono">{formatSize(file.size)}</p>
            </div>
            <button
              type="button"
              className="upload-remove-btn"
              onClick={(e) => {
                e.stopPropagation();
                onFileSelected(null);
                setRejectionMessage(null);
                if (inputRef.current) inputRef.current.value = "";
              }}
              disabled={disabled}
            >
              Remover
            </button>
          </div>
        )}
      </div>

      {rejectionMessage && <p className="upload-error">{rejectionMessage}</p>}

      {showCamera && (
        <CameraCapture
          onCapture={(capturedFile) => {
            setShowCamera(false);
            setRejectionMessage(null);
            onFileSelected(capturedFile);
          }}
          onClose={() => setShowCamera(false)}
        />
      )}
    </section>
  );
}
