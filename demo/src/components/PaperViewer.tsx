import { figureReferences, paperAuthors, paperHighlights, paperSections, paperTitle } from "../data/fixtures";

interface PaperViewerProps {
  highlightedId: string | null;
}

const equationRefs = [
  { id: "eq-1", label: "Eq. (1) Confidence Aggregation" },
  { id: "eq-2", label: "Eq. (2) Citation Convergence" },
  { id: "eq-3", label: "Eq. (3) Plot Agreement" },
  { id: "eq-4", label: "Eq. (4) Contradiction Penalty" },
];

export function PaperViewer({ highlightedId }: PaperViewerProps) {
  return (
    <section className="card paper-viewer">
      <div className="paper-toolbar">
        <span>Journal Draft Preview</span>
        <span className="paper-page">Pages 1 to 2 of 8</span>
      </div>
      <article className="paper-page-body">
        <section className="paper-cover">
          <div>
            <p className="paper-kicker">Scientific Review Draft</p>
            <h1>{paperTitle}</h1>
            <p className="paper-meta">
              Ergo Labs Research Group | Preprint v3 | March 2026
            </p>
            <div className="author-row">
              {paperAuthors.map((author) => (
                <span key={author} className="author-chip">
                  {author}
                </span>
              ))}
            </div>
          </div>
          <aside className="paper-highlight-card">
            <h3>Claim Highlights</h3>
            <ul>
              {paperHighlights.map((highlight) => (
                <li key={highlight}>{highlight}</li>
              ))}
            </ul>
          </aside>
        </section>

        {paperSections.map((section) => (
          <section key={section.heading}>
            <h3>{section.heading}</h3>
            <p>{section.body}</p>
          </section>
        ))}

        <section>
          <h3>Equation Index</h3>
          <ul className="equation-ref-list equation-card-list">
            {equationRefs.map((eq) => (
              <li
                key={eq.id}
                className={highlightedId === eq.id ? "eq-highlight" : ""}
              >
                <strong>{eq.label}</strong>
                <span>Available for context edits in the Math Assistant.</span>
              </li>
            ))}
          </ul>
        </section>

        <section>
          <h3>Figure References</h3>
          <div className="figure-grid">
            {figureReferences.map((figure) => (
              <article key={figure.id} className="figure-card">
                <span>{figure.id.toUpperCase()}</span>
                <strong>{figure.title}</strong>
                <p>{figure.caption}</p>
              </article>
            ))}
          </div>
        </section>

        <section>
          <h3>References</h3>
          <p>
            [1] Structured Verification Graphs for Scientific Reasoning
            (NeurIPS, 2024).
          </p>
          <p>
            [2] Visual Claim Auditing with Latent Trend Models (ICLR, 2025).
          </p>
          <p>
            [3] Symbolic Consistency Checks in Multi-Agent Review (ACL Findings,
            2025).
          </p>
          <p>
            [4] When Citation Similarity Misleads Scientific Validation (arXiv,
            2023).
          </p>
        </section>

        <footer className="paper-footer">Advisor demo manuscript preview. Interaction links on the right remain synced to equation and citation artifacts.</footer>
      </article>
    </section>
  );
}
