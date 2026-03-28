import { PipelineSnapshot } from "../types";

interface StepTrackerProps {
  snapshot: PipelineSnapshot;
}

function statusLabel(status: "pending" | "running" | "complete"): string {
  if (status === "running") {
    return "Running";
  }
  if (status === "complete") {
    return "Complete";
  }
  return "Pending";
}

function formatElapsed(seconds: number): string {
  const minutes = Math.floor(seconds / 60);
  const remaining = seconds % 60;
  return `${minutes}:${remaining.toString().padStart(2, "0")}`;
}

export function StepTracker({ snapshot }: StepTrackerProps) {
  const activeStep = snapshot.steps.find((step) => step.id === snapshot.activeStepId) ?? null;

  return (
    <section className="card step-tracker">
      <div className="step-header-row">
        <h2>Advisor Run Progress</h2>
        <div className="tracker-meta">
          <span className="progress-pill">{snapshot.progressPercent}%</span>
          <span className="elapsed-pill">{formatElapsed(snapshot.elapsedSeconds)}</span>
        </div>
      </div>
      <div className="progress-track" aria-label="advisor progress">
        <div className="progress-fill" style={{ width: `${snapshot.progressPercent}%` }} />
      </div>

      <div className="active-stage-card">
        <span className="active-stage-label">Current Stage</span>
        <strong>{activeStep?.label ?? (snapshot.isComplete ? "Results Ready" : "Waiting to Start")}</strong>
        <p>{activeStep?.deliverable ?? (snapshot.isComplete ? "All advisor artifacts are available for inspection." : "Run the advisor to watch each artifact appear in sequence.")}</p>
      </div>

      <ul className="step-list">
        {snapshot.steps.map((step, index) => (
          <li key={step.id} className={`step-item step-${step.status}`}>
            <div className="step-index">{index + 1}</div>
            <div className="step-copy">
              <div className="step-title-row">
                <strong>{step.label}</strong>
                <span className="step-metric">{step.metric}</span>
              </div>
              <p>{step.summary}</p>
            </div>
            <span className={`step-status status-${step.status}`}>{statusLabel(step.status)}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
