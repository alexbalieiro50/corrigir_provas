import type { ReactNode } from "react";
import "./FiducialCard.css";

interface FiducialCardProps {
  children: ReactNode;
  className?: string;
}

/**
 * Cartão com "marcas de registro" nos cantos, como as marcas fiduciais usadas
 * em folhas de OMR reais para o leitor óptico se orientar. É o elemento de
 * assinatura visual do produto: remete diretamente ao objeto físico que a
 * aplicação lê (o cartão-resposta).
 */
export default function FiducialCard({ children, className = "" }: FiducialCardProps) {
  return (
    <div className={`fiducial-card ${className}`}>
      <span className="fiducial-mark fiducial-tl" aria-hidden="true" />
      <span className="fiducial-mark fiducial-tr" aria-hidden="true" />
      <span className="fiducial-mark fiducial-bl" aria-hidden="true" />
      <span className="fiducial-mark fiducial-br" aria-hidden="true" />
      <div className="fiducial-card-content">{children}</div>
    </div>
  );
}
