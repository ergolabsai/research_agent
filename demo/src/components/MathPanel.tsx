import { FormEvent, useMemo, useState } from "react";
import { chatSeed, equations } from "../data/fixtures";

interface Message {
  role: "agent" | "user";
  text: string;
}

interface MathPanelProps {
  onEquationFocus: (equationId: string) => void;
}

export function MathPanel({ onEquationFocus }: MathPanelProps) {
  const [selectedId, setSelectedId] = useState(equations[0].id);
  const [contextText, setContextText] = useState(equations[0].context);
  const [messages, setMessages] = useState<Message[]>(chatSeed as Message[]);
  const [draft, setDraft] = useState("");

  const selectedEquation = useMemo(
    () => equations.find((eq) => eq.id === selectedId) ?? equations[0],
    [selectedId]
  );

  const onSelectEquation = (equationId: string) => {
    const next = equations.find((eq) => eq.id === equationId);
    if (!next) {
      return;
    }

    setSelectedId(equationId);
    setContextText(next.context);
    onEquationFocus(equationId);
  };

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!draft.trim()) {
      return;
    }

    const userPrompt = draft.trim();
    setMessages((current) => [
      ...current,
      { role: "user", text: userPrompt },
      {
        role: "agent",
        text: `Updated review for ${selectedEquation.id}: this equation remains consistent if your added assumption holds under monotonic residual bounds.`,
      },
    ]);
    setDraft("");
  };

  return (
    <div className="panel-content">
      <h3>Math Assistant</h3>
      <p className="panel-subtitle">
        Select an equation to inspect usage, add context, and chat with the agent for updates.
      </p>

      <div className="math-layout">
        <aside>
          <h4>Equations Found</h4>
          <ul className="equation-list">
            {equations.map((eq) => (
              <li key={eq.id}>
                <button
                  type="button"
                  className={eq.id === selectedId ? "active" : ""}
                  onClick={() => onSelectEquation(eq.id)}
                >
                  <span>{eq.id.toUpperCase()}</span>
                  <small>{eq.usage}</small>
                </button>
              </li>
            ))}
          </ul>
        </aside>

        <section className="equation-detail">
          <h4>{selectedEquation.id.toUpperCase()}</h4>
          <p className="equation-expression">{selectedEquation.equation}</p>
          <p>{selectedEquation.usage}</p>
          <label>
            Additional context / modifications
            <textarea
              value={contextText}
              onChange={(e) => setContextText(e.target.value)}
              rows={4}
            />
          </label>
          <p className="hint-text">{selectedEquation.editableHint}</p>

          <div className="chat-window" aria-live="polite">
            {messages.map((message, idx) => (
              <div key={`${message.role}-${idx}`} className={`chat-bubble ${message.role}`}>
                <strong>{message.role === "agent" ? "Agent" : "You"}</strong>
                <p>{message.text}</p>
              </div>
            ))}
          </div>
          <form onSubmit={onSubmit} className="chat-form">
            <input
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder="Ask the agent to update this equation context..."
            />
            <button type="submit">Send</button>
          </form>
        </section>
      </div>
    </div>
  );
}
