import { plotDiscrepancies } from "../data/fixtures";

function severityClass(level: "low" | "medium" | "high"): string {
  return `severity-${level}`;
}

export function PlotPanel() {
  return (
    <div className="panel-content">
      <h3>Plot Helper</h3>
      <p className="panel-subtitle">
        Visual comparison after figure evaluation: true plot vs predicted plot and discrepancy notes.
      </p>

      <div className="plot-grid">
        <article className="plot-card">
          <h4>True Plot</h4>
          <svg viewBox="0 0 220 120" role="img" aria-label="true plot">
            <polyline
              fill="none"
              stroke="currentColor"
              strokeWidth="3"
              points="8,95 32,84 58,75 85,58 106,42 128,36 152,50 174,61 198,67 214,69"
            />
          </svg>
        </article>

        <article className="plot-card predicted">
          <h4>Predicted Plot</h4>
          <svg viewBox="0 0 220 120" role="img" aria-label="predicted plot">
            <polyline
              fill="none"
              stroke="currentColor"
              strokeWidth="3"
              points="8,96 32,86 58,79 85,65 106,57 128,52 152,56 174,62 198,66 214,67"
            />
          </svg>
        </article>
      </div>

      <h4>Detected Discrepancies</h4>
      <ul className="discrepancy-list">
        {plotDiscrepancies.map((item) => (
          <li key={item.id}>
            <div>
              <strong>{item.title}</strong>
              <p>{item.detail}</p>
            </div>
            <span className={`severity-tag ${severityClass(item.severity)}`}>{item.severity}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
