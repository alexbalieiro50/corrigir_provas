import { useEffect, useRef, useState } from "react";
import "./CameraCapture.css";

interface CameraCaptureProps {
  onCapture: (file: File) => void;
  onClose: () => void;
}

export default function CameraCapture({ onCapture, onClose }: CameraCaptureProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function startCamera() {
      if (!navigator.mediaDevices?.getUserMedia) {
        setError("Este navegador não tem suporte a acesso à câmera.");
        return;
      }
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: { ideal: "environment" }, // câmera traseira em celulares
            width: { ideal: 1920 },
            height: { ideal: 1920 },
          },
          audio: false,
        });
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
          setReady(true);
        }
      } catch (e) {
        setError(
          "Não foi possível acessar a câmera. Verifique se você deu permissão ao navegador " +
            "(ou se outro aplicativo/aba já está usando a câmera)."
        );
      }
    }

    startCamera();

    return () => {
      cancelled = true;
      streamRef.current?.getTracks().forEach((t) => t.stop());
    };
  }, []);

  function handleCapture() {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(
      (blob) => {
        if (!blob) return;
        const file = new File([blob], `captura-camera-${Date.now()}.jpg`, { type: "image/jpeg" });
        streamRef.current?.getTracks().forEach((t) => t.stop());
        onCapture(file);
      },
      "image/jpeg",
      0.92
    );
  }

  function handleClose() {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    onClose();
  }

  return (
    <div className="camera-overlay" role="dialog" aria-label="Capturar cartão-resposta pela câmera">
      <div className="camera-modal">
        <div className="camera-header">
          <span>Posicione o cartão dentro da moldura</span>
          <button className="camera-close-btn" onClick={handleClose} aria-label="Fechar câmera">
            ✕
          </button>
        </div>

        <div className="camera-viewport">
          {error ? (
            <div className="camera-error">{error}</div>
          ) : (
            <>
              <video ref={videoRef} className="camera-video" playsInline muted />
              <div className="camera-frame-guide" aria-hidden="true" />
            </>
          )}
        </div>

        <canvas ref={canvasRef} style={{ display: "none" }} />

        <div className="camera-controls">
          <button className="camera-cancel-btn" onClick={handleClose}>
            Cancelar
          </button>
          <button className="camera-capture-btn" onClick={handleCapture} disabled={!ready || !!error}>
            <span className="camera-capture-btn-dot" />
            Capturar foto
          </button>
        </div>
        <p className="camera-tip">
          Dica: boa iluminação, sem sombras sobre o cartão, e o cartão inteiro visível ajudam bastante na leitura.
        </p>
      </div>
    </div>
  );
}
