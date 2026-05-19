// SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
//
// SPDX-License-Identifier: AGPL-3.0-only

import { createTheme } from "@mui/material/styles";
import { ReactNode } from "react";

// --- MUI theme augmentation: discrete color palette for plots/graphs ---
declare module "@mui/material/styles" {
  interface Palette {
    discrete: string[];
  }
  interface PaletteOptions {
    discrete?: string[];
  }
}

// --- Discrete color palettes (10 colors each) ---

// Matplotlib tab10 — vivid, good on white/light-gray backgrounds
export const TAB10: readonly string[] = [
  "#1f77b4", // blue
  "#ff7f0e", // orange
  "#2ca02c", // green
  "#d62728", // red
  "#9467bd", // purple
  "#8c564b", // brown
  "#e377c2", // pink
  "#7f7f7f", // gray
  "#bcbd22", // olive
  "#17becf", // cyan
];

// Muted blues/golds — professional light backgrounds
const PROFESSIONAL_LIGHT: readonly string[] = [
  "#2E5090", // navy
  "#E8A425", // gold
  "#3A7D44", // forest
  "#C44E52", // brick
  "#7B68AE", // slate purple
  "#C97B3A", // copper
  "#D17BA2", // mauve
  "#6B6B6B", // charcoal
  "#A3A832", // moss
  "#2B9EB3", // teal
];

// High-contrast monochrome accents — minimal light backgrounds
const MINIMAL_LIGHT: readonly string[] = [
  "#222222", // black
  "#E45C3A", // vermillion
  "#2A7F62", // emerald
  "#3269A8", // cobalt
  "#8B5CF6", // violet
  "#D97706", // amber
  "#0D9488", // teal
  "#6B7280", // gray
  "#B45309", // rust
  "#7C3AED", // indigo
];

// Bright pastels — dark neutral backgrounds
const DARK_DEFAULT: readonly string[] = [
  "#60A5FA", // sky blue
  "#F97316", // vivid orange
  "#34D399", // emerald
  "#F87171", // coral red
  "#A78BFA", // lavender
  "#FB923C", // peach
  "#F472B6", // pink
  "#9CA3AF", // silver
  "#FACC15", // yellow
  "#22D3EE", // cyan
];

// Nord Aurora + Frost — Nord dark backgrounds
const NORD_DARK: readonly string[] = [
  "#88C0D0", // frost blue
  "#EBCB8B", // aurora yellow
  "#A3BE8C", // aurora green
  "#BF616A", // aurora red
  "#B48EAD", // aurora purple
  "#D08770", // aurora orange
  "#81A1C1", // frost
  "#8FBCBB", // teal frost
  "#5E81AC", // deep frost
  "#D8DEE9", // snow
];

// Dracula palette — Dracula dark backgrounds
const DRACULA_DARK: readonly string[] = [
  "#8BE9FD", // cyan
  "#FFB86C", // orange
  "#50FA7B", // green
  "#FF5555", // red
  "#BD93F9", // purple
  "#FF79C6", // pink
  "#F1FA8C", // yellow
  "#6272A4", // comment
  "#8BE9FD", // cyan alt
  "#F8F8F2", // foreground
];

export const discretePalettes: Record<ThemeName, readonly string[]> = {
  "light-default": TAB10,
  "light-professional": PROFESSIONAL_LIGHT,
  "light-minimal": MINIMAL_LIGHT,
  "dark-default": DARK_DEFAULT,
  "dark-nord": NORD_DARK,
  "dark-dracula": DRACULA_DARK,
};

export type ThemeName =
  | "light-default"
  | "light-professional"
  | "light-minimal"
  | "dark-default"
  | "dark-nord"
  | "dark-dracula";

interface ThemeColors {
  primary: {
    main: string;
    light: string;
    dark: string;
  };
  secondary: {
    main: string;
    light: string;
    dark: string;
  };
  background: {
    default: string;
    paper: string;
  };
  text: {
    primary: string;
    secondary: string;
  };
  divider: string;
}

// Light Mode Palettes
const lightDefault: ThemeColors = {
  primary: {
    main: "#1976D2",
    light: "#42A5F5",
    dark: "#1565C0",
  },
  secondary: {
    main: "#DC004E",
    light: "#F05545",
    dark: "#9A0036",
  },
  background: {
    default: "#FAFAFA",
    paper: "#FFFFFF",
  },
  text: {
    primary: "#212121",
    secondary: "#757575",
  },
  divider: "#BDBDBD",
};

const lightProfessional: ThemeColors = {
  primary: {
    main: "#2E5090",
    light: "#5B7CB8",
    dark: "#1A3A5C",
  },
  secondary: {
    main: "#E8A425",
    light: "#F5C261",
    dark: "#C68D0F",
  },
  background: {
    default: "#F5F5F5",
    paper: "#FFFFFF",
  },
  text: {
    primary: "#1E1E1E",
    secondary: "#666666",
  },
  divider: "#D0D0D0",
};

const lightMinimal: ThemeColors = {
  primary: {
    main: "#000000",
    light: "#424242",
    dark: "#000000",
  },
  secondary: {
    main: "#757575",
    light: "#BDBDBD",
    dark: "#424242",
  },
  background: {
    default: "#FEFEFE",
    paper: "#FFFFFF",
  },
  text: {
    primary: "#000000",
    secondary: "#858585",
  },
  divider: "#E0E0E0",
};

// Dark Mode Palettes
const darkDefault: ThemeColors = {
  primary: {
    main: "#90CAF9",
    light: "#BBDEFB",
    dark: "#42A5F5",
  },
  secondary: {
    main: "#F48FB1",
    light: "#F8BBD0",
    dark: "#EC407A",
  },
  background: {
    default: "#1e1e1e",
    paper: "#222222",
  },
  text: {
    primary: "#FFFFFF",
    secondary: "#B0B0B0",
  },
  divider: "#90CAF920",
};

const darkNord: ThemeColors = {
  primary: {
    main: "#88C0D0",
    light: "#A3BE8C",
    dark: "#5E81AC",
  },
  secondary: {
    main: "#BF616A",
    light: "#D08770",
    dark: "#A3BE8C",
  },
  background: {
    default: "#2E3440",
    paper: "#3B4252",
  },
  text: {
    primary: "#ECEFF4",
    secondary: "#D0D0D0",
  },
  divider: "#434C5E",
};

const darkDracula: ThemeColors = {
  primary: {
    main: "#8BE9FD",
    light: "#A4EFFF",
    dark: "#5FD9FF",
  },
  secondary: {
    main: "#FF79C6",
    light: "#FF99DD",
    dark: "#FF5FA0",
  },
  background: {
    default: "#282A36",
    paper: "#21222C",
  },
  text: {
    primary: "#F8F8F2",
    secondary: "#B8B8BF",
  },
  divider: "#44475A",
};

export const themeColors: Record<ThemeName, ThemeColors> = {
  "light-default": lightDefault,
  "light-professional": lightProfessional,
  "light-minimal": lightMinimal,
  "dark-default": darkDefault,
  "dark-nord": darkNord,
  "dark-dracula": darkDracula,
};

export const themeGroups = {
  light: [
    "light-default",
    "light-professional",
    "light-minimal",
  ] as ThemeName[],
  dark: ["dark-default", "dark-nord", "dark-dracula"] as ThemeName[],
};

export const createAppTheme = (themeName: ThemeName) => {
  const colors = themeColors[themeName];
  const isDark = themeName.startsWith("dark");

  return createTheme({
    palette: {
      mode: isDark ? "dark" : "light",
      primary: {
        main: colors.primary.main,
        light: colors.primary.light,
        dark: colors.primary.dark,
      },
      secondary: {
        main: colors.secondary.main,
        light: colors.secondary.light,
        dark: colors.secondary.dark,
      },
      background: {
        default: colors.background.default,
        paper: colors.background.paper,
      },
      text: {
        primary: colors.text.primary,
        secondary: colors.text.secondary,
      },
      divider: colors.divider,
      discrete: [...discretePalettes[themeName]],
    },
    typography: {
      fontFamily:
        '"Segoe UI", "Roboto", "Oxygen", "Ubuntu", "Cantarell", "sans-serif"',
      h1: {
        fontSize: "2rem",
        fontWeight: 600,
      },
      h2: {
        fontSize: "1.5rem",
        fontWeight: 600,
      },
      h3: {
        fontSize: "1.25rem",
        fontWeight: 600,
      },
      body1: {
        fontSize: "0.95rem",
        lineHeight: 1.6,
      },
      body2: {
        fontSize: "0.875rem",
        lineHeight: 1.5,
      },
    },
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: "none",
            fontWeight: 500,
            borderRadius: "8px",
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: "12px",
            boxShadow: isDark
              ? "0 4px 20px rgba(0, 0, 0, 0.4)"
              : "0 2px 8px rgba(0, 0, 0, 0.1)",
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            borderRadius: "12px",
          },
        },
      },
      MuiDrawer: {
        styleOverrides: {
          paper: {
            backgroundColor: isDark ? "#222222" : colors.background.paper,
            borderRight: "none",
          },
        },
      },
      MuiAppBar: {
        styleOverrides: {
          root: {
            backgroundColor: "transparent",
            boxShadow: "none",
            borderBottom: "none",
          },
        },
      },
      MuiIconButton: {
        styleOverrides: {
          root: {
            borderRadius: "8px",
          },
        },
      },
    },
  });
};

export interface AppThemeProviderProps {
  children: ReactNode;
  themeName?: ThemeName;
}
