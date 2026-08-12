import "./Header.css";

export default function Header() {
  return (
    <header className="app-header">
      <div className="app-header-inner">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">
            <span className="brand-mark-dot" />
          </span>
          <div>
            <h1>Corretor OMR</h1>
            <p className="subtitle">Correção automática de cartões-resposta</p>
          </div>
        </div>
      </div>
    </header>
  );
}
