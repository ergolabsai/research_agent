import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AdvisorStep, PipelineSnapshot } from "../types";

const baseSteps: AdvisorStep[] = [
  {
    id: "make_context",
    label: "Context",
    summary: "Extracting domain context and manuscript metadata.",
    metric: "12 manuscript signals",
    deliverable: "Domain summary + manuscript profile",
    status: "pending",
    durationMs: 1600,
  },
  {
    id: "gather_papers",
    label: "Gather Papers",
    summary: "Collecting related literature and abstracts.",
    metric: "18 papers retrieved",
    deliverable: "Scored search set + abstract bundle",
    status: "pending",
    durationMs: 2000,
  },
  {
    id: "map_logic",
    label: "Map Logic",
    summary: "Building claim dependency map from core arguments.",
    metric: "7 linked claims",
    deliverable: "Logical dependency graph",
    status: "pending",
    durationMs: 1900,
  },
  {
    id: "find_evidence",
    label: "Evidence",
    summary: "Linking each logical step to textual evidence.",
    metric: "24 evidence spans",
    deliverable: "Claim-to-evidence trace",
    status: "pending",
    durationMs: 1800,
  },
  {
    id: "evaluate_figures",
    label: "Plot",
    summary: "Comparing true and predicted visual trajectories.",
    metric: "3 figures audited",
    deliverable: "Figure discrepancy report",
    status: "pending",
    durationMs: 2400,
  },
  {
    id: "evaluate_math",
    label: "Math",
    summary: "Validating equations and symbolic assumptions.",
    metric: "4 equations traced",
    deliverable: "Equation consistency notes",
    status: "pending",
    durationMs: 2200,
  },
  {
    id: "score_papers",
    label: "Citations",
    summary: "Scoring related papers for relevance and convergence.",
    metric: "4 papers surfaced",
    deliverable: "Relevancy + convergence ranking",
    status: "pending",
    durationMs: 2100,
  },
  {
    id: "compile_results",
    label: "Compile",
    summary: "Synthesizing confidence score and final recommendation.",
    metric: "0.82 confidence",
    deliverable: "Final advisor recommendation",
    status: "pending",
    durationMs: 1700,
  },
];

function calculateProgress(steps: AdvisorStep[]): number {
  const completeCount = steps.filter((s) => s.status === "complete").length;
  return Math.round((completeCount / steps.length) * 100);
}

export function useDemoPipeline() {
  const [steps, setSteps] = useState<AdvisorStep[]>(baseSteps);
  const [isRunning, setIsRunning] = useState(false);
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const timersRef = useRef<number[]>([]);
  const intervalRef = useRef<number | null>(null);

  const clearTimers = useCallback(() => {
    timersRef.current.forEach((t) => window.clearTimeout(t));
    timersRef.current = [];
    if (intervalRef.current !== null) {
      window.clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const reset = useCallback(() => {
    clearTimers();
    setIsRunning(false);
    setActiveIndex(null);
    setElapsedSeconds(0);
    setSteps(baseSteps.map((step) => ({ ...step, status: "pending" })));
  }, [clearTimers]);

  const run = useCallback(() => {
    clearTimers();
    setIsRunning(true);
    setActiveIndex(0);
    setElapsedSeconds(0);
    setSteps(baseSteps.map((step, idx) => ({ ...step, status: idx === 0 ? "running" : "pending" })));
    intervalRef.current = window.setInterval(() => {
      setElapsedSeconds((current) => current + 1);
    }, 1000);

    let elapsed = 0;
    baseSteps.forEach((step, idx) => {
      elapsed += step.durationMs;
      const timer = window.setTimeout(() => {
        setSteps((current) =>
          current.map((item, itemIdx) => {
            if (itemIdx < idx + 1) {
              return { ...item, status: "complete" };
            }
            if (itemIdx === idx + 1) {
              return { ...item, status: "running" };
            }
            return item;
          })
        );

        if (idx === baseSteps.length - 1) {
          setIsRunning(false);
          setActiveIndex(null);
          if (intervalRef.current !== null) {
            window.clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
          return;
        }

        setActiveIndex(idx + 1);
      }, elapsed);
      timersRef.current.push(timer);
    });
  }, [clearTimers]);

  useEffect(() => () => clearTimers(), [clearTimers]);

  const snapshot: PipelineSnapshot = useMemo(
    () => ({
      steps,
      activeStepId: activeIndex !== null ? steps[activeIndex]?.id ?? null : null,
      progressPercent: calculateProgress(steps),
      isRunning,
      isComplete: steps.every((s) => s.status === "complete"),
      elapsedSeconds,
    }),
    [activeIndex, elapsedSeconds, isRunning, steps]
  );

  const unlocks = useMemo(
    () => ({
      plot: steps.find((s) => s.id === "evaluate_figures")?.status === "complete",
      math: steps.find((s) => s.id === "evaluate_math")?.status === "complete",
      citations: steps.find((s) => s.id === "score_papers")?.status === "complete",
    }),
    [steps]
  );

  return {
    snapshot,
    unlocks,
    run,
    reset,
  };
}
