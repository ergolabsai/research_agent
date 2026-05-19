// SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
//
// SPDX-License-Identifier: AGPL-3.0-only

import {
  Box,
  Divider,
  IconButton,
  TextField,
  Typography,
} from "@mui/material";
import { Send as SendIcon } from "@mui/icons-material";
import { FormEvent, ReactNode, useCallback, useEffect, useRef, useState } from "react";
import type { AgentChatCategory, AgentChatMessage } from "../types";
import { MarkdownRenderer } from "./MarkdownRenderer";

interface ChatBubble {
  role: "user" | "agent";
  text: string;
}

const MIN_CHAT_HEIGHT = 100;
const MAX_CHAT_HEIGHT = 500;
const DEFAULT_CHAT_HEIGHT = 190;
const STORAGE_KEY = "agent-chat-height";

function readStoredHeight(): number {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw != null) {
      const n = Number(raw);
      if (n >= MIN_CHAT_HEIGHT && n <= MAX_CHAT_HEIGHT) return n;
    }
  } catch { /* ignore */ }
  return DEFAULT_CHAT_HEIGHT;
}

export interface AgentChatProps {
  /** Pre-loaded messages from the API for this job */
  allMessages: AgentChatMessage[];
  /** Which agent category to filter by */
  category: AgentChatCategory;
  /** Currently selected target id (e.g. equation node id) — filters messages */
  targetId: string | null;
  /** Placeholder text for the input */
  placeholder?: string;
}

export function AgentChat({
  allMessages,
  category,
  targetId,
  placeholder = "Ask the agent...",
}: AgentChatProps) {
  const chatListRef = useRef<HTMLDivElement>(null);
  const [localMessages, setLocalMessages] = useState<ChatBubble[]>([]);
  const [draft, setDraft] = useState("");
  const prevTargetRef = useRef<string | null>(null);
  const [chatHeight, setChatHeight] = useState(readStoredHeight);
  const dragState = useRef<{ startY: number; startHeight: number } | null>(null);

  // Reset local messages when target changes
  useEffect(() => {
    if (prevTargetRef.current !== targetId) {
      setLocalMessages([]);
      prevTargetRef.current = targetId;
    }
  }, [targetId]);

  // Filter API messages by category + target
  const apiMessages: ChatBubble[] = allMessages
    .filter(
      (m) =>
        m.category === category &&
        (targetId == null || m.target_id === targetId),
    )
    .map((m) => ({ role: m.role, text: m.text }));

  const displayedMessages = [...apiMessages, ...localMessages];

  useEffect(() => {
    const container = chatListRef.current;
    if (!container) return;
    container.scrollTo({ top: container.scrollHeight, behavior: "smooth" });
  }, [displayedMessages.length]);

  const handleSend = (e: FormEvent) => {
    e.preventDefault();
    if (!draft.trim()) return;
    setLocalMessages((prev) => [
      ...prev,
      { role: "user", text: draft.trim() },
    ]);
    setDraft("");
  };

  // Drag-to-resize handlers
  const handleDragStart = useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      dragState.current = { startY: e.clientY, startHeight: chatHeight };
      e.currentTarget.setPointerCapture(e.pointerId);
    },
    [chatHeight],
  );

  const handleDragMove = useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      if (!dragState.current) return;
      // Dragging up = negative deltaY = taller chat
      const deltaY = dragState.current.startY - e.clientY;
      const next = Math.min(
        MAX_CHAT_HEIGHT,
        Math.max(MIN_CHAT_HEIGHT, dragState.current.startHeight + deltaY),
      );
      setChatHeight(next);
    },
    [],
  );

  const handleDragEnd = useCallback(() => {
    if (dragState.current) {
      try { localStorage.setItem(STORAGE_KEY, String(chatHeight)); } catch { /* ignore */ }
    }
    dragState.current = null;
  }, [chatHeight]);

  return (
    <Box sx={{ flexShrink: 0 }}>
      {/* Drag handle */}
      <Box
        onPointerDown={handleDragStart}
        onPointerMove={handleDragMove}
        onPointerUp={handleDragEnd}
        onPointerCancel={handleDragEnd}
        sx={{
          height: 10,
          cursor: "ns-resize",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          "&:hover > div": { bgcolor: "primary.main" },
          touchAction: "none",
        }}
      >
        <Box
          sx={{
            width: 40,
            height: 3,
            borderRadius: 1.5,
            bgcolor: "divider",
            transition: "background-color 150ms",
          }}
        />
      </Box>

      <Divider />

      <Typography variant="subtitle2" fontWeight={700} sx={{ mt: 1, mb: 1 }}>
        Agent Chat
      </Typography>
      <Box
        ref={chatListRef}
        sx={{
          display: "flex",
          flexDirection: "column",
          gap: 0.75,
          height: chatHeight,
          overflow: "auto",
          pr: 0.5,
        }}
      >
        {displayedMessages.length === 0 && (
          <Typography variant="caption" color="text.secondary">
            No messages yet. Ask the agent a question.
          </Typography>
        )}
        {displayedMessages.map((m, i) => (
          <Box
            key={`${m.role}-${i}`}
            sx={{
              alignSelf: m.role === "user" ? "flex-end" : "flex-start",
              maxWidth: "88%",
              p: 1,
              borderRadius: 2,
              bgcolor: m.role === "user" ? "primary.main" : "action.selected",
              color:
                m.role === "user" ? "primary.contrastText" : "text.primary",
            }}
          >
            <Typography variant="caption" fontWeight={700} display="block">
              {m.role === "agent" ? "Agent" : "You"}
            </Typography>
            {m.role === "agent" ? (
              <Box sx={{ fontSize: "0.875rem", "& h3": { fontSize: "0.9rem", mt: 1.5, mb: 0.25 }, "& p": { fontSize: "0.875rem", mb: 0.5 }, "& li": { fontSize: "0.875rem" }, "& ul": { pl: 1.5 } }}>
                <MarkdownRenderer>{m.text}</MarkdownRenderer>
              </Box>
            ) : (
              <Typography variant="body2">{m.text}</Typography>
            )}
          </Box>
        ))}
      </Box>
      <Box
        component="form"
        onSubmit={handleSend}
        sx={{ display: "flex", gap: 1, mt: 1 }}
      >
        <TextField
          size="small"
          fullWidth
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={placeholder}
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
  );
}

/**
 * Layout wrapper for agent tabs with pinned AgentChat at the bottom.
 * Scrollable content area on top, AgentChat fixed at bottom.
 */
export function TabContentWithChat({
  children,
  chatProps,
}: {
  children: ReactNode;
  chatProps: AgentChatProps;
}) {
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        minHeight: 0,
      }}
    >
      <Box sx={{ flex: 1, minHeight: 0, overflow: "auto" }}>{children}</Box>
      <AgentChat {...chatProps} />
    </Box>
  );
}
