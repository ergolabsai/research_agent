import { citations } from "../data/fixtures";

export function CitationsPanel() {
  return (
    <div className="panel-content">
      <h3>Citation Review</h3>
      <p className="panel-subtitle">
        Related papers ranked by relevancy and convergence with expandable agent
        commentary.
      </p>

      <div className="citation-list">
        {citations.map((paper) => (
          <details key={paper.id}>
            <summary>
              <div className="citation-headline">
                <strong>{paper.title}</strong>
                <span>
                  {paper.venue} {paper.year}
                </span>
              </div>
              <div className="citation-scores">
                <span>Relevancy {paper.relevancy.toFixed(2)}</span>
                <span>Convergence {paper.convergence.toFixed(2)}</span>
              </div>
              <div className="citation-bar-row" aria-hidden="true">
                <div>
                  <small>Relevancy</small>
                  <div className="score-bar">
                    <div className="score-bar-fill relevancy" style={{ width: `${paper.relevancy * 100}%` }} />
                  </div>
                </div>
                <div>
                  <small>Convergence</small>
                  <div className="score-bar">
                    <div
                      className={`score-bar-fill ${paper.convergence >= 0 ? "convergence-positive" : "convergence-negative"}`}
                      style={{ width: `${Math.abs(paper.convergence) * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            </summary>
            <div className="citation-details">
              <p>
                <strong>Agent context:</strong> {paper.context}
              </p>
              <p>
                <strong>Comparison to our conclusions:</strong>{" "}
                {paper.comparison}
              </p>
            </div>
          </details>
        ))}
      </div>
    </div>
  );
}
