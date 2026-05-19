// SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
//
// SPDX-License-Identifier: AGPL-3.0-only

import {
  ToggleButtonGroup,
  ToggleButton,
  Tooltip,
  useTheme,
} from "@mui/material";
import {
  Article as RichIcon,
  DataObject as JsonIcon,
  Code as LatexIcon,
} from "@mui/icons-material";

export type ViewMode = "rich" | "json" | "latex";

interface ViewModeToggleProps {
  mode: ViewMode;
  onChange: (mode: ViewMode) => void;
}

export const ViewModeToggle = ({ mode, onChange }: ViewModeToggleProps) => {
  const theme = useTheme();

  return (
    <ToggleButtonGroup
      value={mode}
      exclusive
      onChange={(_e, val) => {
        if (val) onChange(val as ViewMode);
      }}
      sx={{
        height: 50,
        width: 260,
        flexShrink: 0,
        borderRadius: "12px",
        border: "1px solid " + theme.palette.divider,
        background: `linear-gradient(135deg, ${theme.palette.primary.main}10 0%, ${theme.palette.secondary.main}20 100%)`,
        overflow: "hidden",
        "& .MuiToggleButtonGroup-grouped": {
          border: "none",
          borderRadius: "0 !important",
          "&:not(:last-of-type)": {
            borderRight: "1px solid " + theme.palette.divider,
          },
        },
        "& .MuiToggleButton-root": {
          flex: 1,
          textTransform: "none",
          fontSize: "0.8rem",
          fontWeight: 600,
          gap: 0.75,
          color: theme.palette.text.secondary,
          background: "transparent",
          "&.Mui-selected": {
            color: theme.palette.primary.main,
            background: `${theme.palette.primary.main}18`,
          },
        },
      }}
    >
      <Tooltip title="Formatted view">
        <ToggleButton value="rich">
          <RichIcon fontSize="small" /> Rich
        </ToggleButton>
      </Tooltip>
      <Tooltip title="Structured JSON source">
        <ToggleButton value="json">
          <JsonIcon fontSize="small" /> JSON
        </ToggleButton>
      </Tooltip>
      <Tooltip title="LaTeX source code">
        <ToggleButton value="latex">
          <LatexIcon fontSize="small" /> LaTeX
        </ToggleButton>
      </Tooltip>
    </ToggleButtonGroup>
  );
};
