import { useMemo, useState } from "react";
import { PaperViewer } from "./components/PaperViewer";
import { RightPanel, PanelTab } from "./components/RightPanel";
import { StepTracker } from "./components/StepTracker";
import { useDemoPipeline } from "./hooks/useDemoPipeline";

function getRecommendedTab(unlocks: { plot: boolean; math: boolean; citations: boolean }): PanelTab {
  if (unlocks.citations) {
    return "citations";
  }
  if (unlocks.math) {
    return "math";
  }
  return "plot";
}

export default function App() {
  const { snapshot, unlocks, run, reset } = useDemoPipeline();
  const [activeTab, setActiveTab] = useState<PanelTab>("plot");
  const [focusedEquationId, setFocusedEquationId] = useState<string | null>(null);

  const isAnyPanelUnlocked = useMemo(() => unlocks.plot || unlocks.math || unlocks.citations, [unlocks]);

  const startRun = () => {
    setFocusedEquationId(null);
    setActiveTab("plot");
    run();
  };

  const replay = () => {
    reset();
    setFocusedEquationId(null);
    setActiveTab("plot");
  };

  const onSelectTab = (tab: PanelTab) => {
    setActiveTab(tab);
  };

  const recommendedTab = getRecommendedTab(unlocks);

  return (
    <div className="app-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">Ergo Labs Advisor</p>
          <h1>End-to-End Product Demo</h1>
          <p>
            This standalone experience simulates the full advisor workflow without backend calls. Track step
            progress, inspect figure discrepancies, revise equations, and review literature convergence.
          </p>
          <div className="hero-status-row">
            <span className="hero-status-card">Scenario: evidence-heavy manuscript</span>
            <span className="hero-status-card">Workflow: 8 staged advisor agents</span>
            <span className="hero-status-card">State: {snapshot.isComplete ? "review ready" : snapshot.isRunning ? "analysis running" : "waiting"}</span>
          </div>
        </div>
        <div className="hero-actions">
          <button type="button" onClick={startRun} disabled={snapshot.isRunning}>
            {snapshot.isRunning ? "Advisor Running..." : "Run Advisor"}
          </button>
          <button type="button" className="secondary" onClick={replay}>
            Replay Demo
          </button>
          <p>
            Suggested next panel: <strong>{recommendedTab === "plot" ? "Plot Helper" : recommendedTab === "math" ? "Math Assistant" : "Citation Review"}</strong>
          </p>
        </div>
      </header>

      <main className="workspace-grid">
        <PaperViewer highlightedId={focusedEquationId} />

        <section className="center-column">
          <StepTracker snapshot={snapshot} />
          <section className="card quick-notes">
            <h2>Advisor Session Notes</h2>
            <ul>
              <li>Document mode: fully rendered manuscript preview (non-editable).</li>
              <li>Pipeline status: {snapshot.isComplete ? "Completed" : snapshot.isRunning ? "In progress" : "Idle"}.</li>
              <li>
                Side tools: {isAnyPanelUnlocked ? "at least one panel unlocked" : "panels unlock as pipeline completes"}.
              </li>
              <li>Current review tone: evidence-grounded, discrepancy-sensitive, and citation-aware.</li>
            </ul>
          </section>
        </section>

        <RightPanel
          selectedTab={activeTab}
          unlocks={unlocks}
          onSelectTab={onSelectTab}
          onEquationFocus={setFocusedEquationId}
        />
      </main>
    </div>
  );
}
