import { CitationsPanel } from "./CitationsPanel";
import { MathPanel } from "./MathPanel";
import { PlotPanel } from "./PlotPanel";

export type PanelTab = "plot" | "math" | "citations";

interface RightPanelProps {
  selectedTab: PanelTab;
  unlocks: {
    plot: boolean;
    math: boolean;
    citations: boolean;
  };
  onSelectTab: (tab: PanelTab) => void;
  onEquationFocus: (equationId: string) => void;
}

function tabLabel(tab: PanelTab): string {
  if (tab === "plot") {
    return "Plot Helper";
  }
  if (tab === "math") {
    return "Math Assistant";
  }
  return "Citation Review";
}

export function RightPanel({
  selectedTab,
  unlocks,
  onSelectTab,
  onEquationFocus,
}: RightPanelProps) {
  const lockState = {
    plot: !unlocks.plot,
    math: !unlocks.math,
    citations: !unlocks.citations,
  };

  return (
    <section className="card right-panel">
      <div className="right-panel-tabs">
        {(["plot", "math", "citations"] as const).map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => onSelectTab(tab)}
            className={selectedTab === tab ? "active" : ""}
            disabled={lockState[tab]}
            title={lockState[tab] ? `Unlocks after ${tabLabel(tab)} step` : `Open ${tabLabel(tab)}`}
          >
            {tabLabel(tab)}
          </button>
        ))}
      </div>

      {selectedTab === "plot" &&
        (unlocks.plot ? (
          <PlotPanel />
        ) : (
          <div className="panel-locked-state">
            <h3>Plot Helper Locked</h3>
            <p>Figure analysis has not completed yet. Once the plot step finishes, the true curve, predicted curve, and discrepancy notes will appear here.</p>
          </div>
        ))}
      {selectedTab === "math" &&
        (unlocks.math ? (
          <MathPanel onEquationFocus={onEquationFocus} />
        ) : (
          <div className="panel-locked-state">
            <h3>Math Assistant Locked</h3>
            <p>Equation extraction and symbolic validation are still pending. This area unlocks when the advisor has traced equations from the manuscript.</p>
          </div>
        ))}
      {selectedTab === "citations" &&
        (unlocks.citations ? (
          <CitationsPanel />
        ) : (
          <div className="panel-locked-state">
            <h3>Citation Review Locked</h3>
            <p>Related papers have not been scored yet. After literature scoring, this panel will show convergence signals and expandable paper comparisons.</p>
          </div>
        ))}
    </section>
  );
}
