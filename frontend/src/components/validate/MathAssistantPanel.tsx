import {
  Box,
  Typography,
  Stack,
  Chip,
  Divider,
  TextField,
  IconButton,
} from "@mui/material";
import {
  CheckCircle as ValidIcon,
  Cancel as InvalidIcon,
  Send as SendIcon,
} from "@mui/icons-material";
import { useState, FormEvent, useRef, useEffect } from "react";
import { ValidationResult } from "../../types";

interface MathAssistantPanelProps {
  result: ValidationResult | null;
}

interface ChatMessage {
  role: "agent" | "user";
  text: string;
}

const INITIAL_MESSAGES: ChatMessage[] = [
  {
    role: "agent",
    text: "I've traced the equations in this paper. Select one below to inspect its validation details and add context.",
  },
];

export function MathAssistantPanel({ result }: MathAssistantPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>(INITIAL_MESSAGES);
  const [draft, setDraft] = useState("");
  const [selectedEq, setSelectedEq] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Collect all math validations across all step validations
  const allMath = result
    ? Object.values(result.step_validations).flatMap(
        (v: any) => v.math_validations ?? [],
      )
    : [];

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSelectEquation = (ref: string) => {
    setSelectedEq(ref);
    const eq = allMath.find((m: any) => m.equation_reference === ref);
    if (eq) {
      setMessages((prev) => [
        ...prev,
        {
          role: "agent",
          text: `Selected ${ref}: ${eq.calculation_valid ? "validation passed" : "validation failed"}. ${eq.details}`,
        },
      ]);
    }
  };

  const handleSend = (e: FormEvent) => {
    e.preventDefault();
    if (!draft.trim()) return;
    const userMsg = draft.trim();
    setMessages((prev) => [
      ...prev,
      { role: "user", text: userMsg },
      {
        role: "agent",
        text: `Noted. For ${selectedEq ?? "the selected equation"}, the context has been recorded. Re-run the pipeline with updated assumptions to recompute confidence.`,
      },
    ]);
    setDraft("");
  };

  return (
    <Box sx={{ p: 2, display: "flex", flexDirection: "column", gap: 2 }}>
      {/* Equation list */}
      <Box>
        <Typography variant="subtitle2" gutterBottom fontWeight={600}>
          Equations Found
        </Typography>
        {allMath.length === 0 ? (
          <Typography variant="body2" color="text.secondary">
            No math validation data available.
          </Typography>
        ) : (
          <Stack spacing={1}>
            {allMath.map((m: any, i: number) => (
              <Box
                key={i}
                onClick={() => handleSelectEquation(m.equation_reference)}
                sx={{
                  p: 1.5,
                  borderRadius: 1,
                  border: 1,
                  borderColor:
                    selectedEq === m.equation_reference
                      ? "primary.main"
                      : "divider",
                  cursor: "pointer",
                  bgcolor:
                    selectedEq === m.equation_reference
                      ? "action.selected"
                      : "transparent",
                  "&:hover": { bgcolor: "action.hover" },
                  transition: "all 0.2s",
                }}
              >
                <Stack
                  direction="row"
                  justifyContent="space-between"
                  alignItems="center"
                  sx={{ mb: 0.5 }}
                >
                  <Typography variant="body2" fontWeight={600}>
                    {m.equation_reference}
                  </Typography>
                  <Chip
                    label={m.calculation_valid ? "Valid" : "Invalid"}
                    size="small"
                    color={m.calculation_valid ? "success" : "error"}
                    icon={
                      m.calculation_valid ? (
                        <ValidIcon fontSize="small" />
                      ) : (
                        <InvalidIcon fontSize="small" />
                      )
                    }
                  />
                </Stack>
                <Typography
                  variant="caption"
                  color="text.secondary"
                  display="block"
                >
                  {m.details}
                </Typography>
                {m.formula_used && (
                  <Typography
                    variant="caption"
                    color="primary.main"
                    display="block"
                    sx={{ mt: 0.25 }}
                  >
                    Formula: {m.formula_used}
                  </Typography>
                )}
              </Box>
            ))}
          </Stack>
        )}
      </Box>

      <Divider />

      {/* Chat UI */}
      <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
        <Typography variant="subtitle2" fontWeight={600}>
          Agent Chat
        </Typography>
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            gap: 0.75,
            maxHeight: 220,
            overflow: "auto",
            pr: 0.5,
          }}
        >
          {messages.map((m, i) => (
            <Box
              key={i}
              sx={{
                alignSelf: m.role === "user" ? "flex-end" : "flex-start",
                maxWidth: "88%",
                p: 1.25,
                borderRadius: 2,
                bgcolor:
                  m.role === "user" ? "primary.main" : "action.selected",
                color:
                  m.role === "user" ? "primary.contrastText" : "text.primary",
              }}
            >
              <Typography
                variant="caption"
                fontWeight={700}
                display="block"
                sx={{ mb: 0.25, opacity: 0.75 }}
              >
                {m.role === "agent" ? "Agent" : "You"}
              </Typography>
              <Typography variant="body2" sx={{ lineHeight: 1.4 }}>
                {m.text}
              </Typography>
            </Box>
          ))}
          <div ref={chatEndRef} />
        </Box>
        <Box
          component="form"
          onSubmit={handleSend}
          sx={{ display: "flex", gap: 1, mt: 0.5 }}
        >
          <TextField
            size="small"
            fullWidth
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Ask the agent about an equation..."
          />
          <IconButton
            type="submit"
            size="small"
            color="primary"
            disabled={!draft.trim()}
          >
            <SendIcon />
          </IconButton>
        </Box>
      </Box>
    </Box>
  );
}
