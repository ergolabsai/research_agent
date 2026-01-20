// frontend/utils/theme.ts
import { createTheme } from "@mui/material/styles";

/* ---------- DARK THEME ---------- */

export const darkTheme = createTheme({
  palette: {
    mode: "dark",

    primary: {
      main: "#90caf9",
      light: "#e3f2fd",
      dark: "#42a5f5",
      contrastText: "#000000",
    },

    secondary: {
      main: "#f48fb1",
      light: "#f8bbd0",
      dark: "#c2185b",
      contrastText: "#000000",
    },

    error: {
      main: "#f44336",
    },

    warning: {
      main: "#ff9800",
    },

    info: {
      main: "#29b6f6",
    },

    success: {
      main: "#66bb6a",
    },

    background: {
      default: "#121212", // app background
      paper: "#1e1e1e",   // cards, modals, menus
    },

    text: {
      primary: "#ffffff",
      secondary: "rgba(255, 255, 255, 0.7)",
      disabled: "rgba(255, 255, 255, 0.5)",
    },

    divider: "rgba(255, 255, 255, 0.12)",

    action: {
      active: "#ffffff",
      hover: "rgba(255, 255, 255, 0.08)",
      selected: "rgba(255, 255, 255, 0.16)",
      disabled: "rgba(255, 255, 255, 0.3)",
      disabledBackground: "rgba(255, 255, 255, 0.12)",
      focus: "rgba(255, 255, 255, 0.12)",
    },
  },
});

/* ---------- LIGHT THEME ---------- */

export const lightTheme = createTheme({
  palette: {
    mode: "light",

    primary: {
      main: "#1976d2",
      light: "#63a4ff",
      dark: "#004ba0",
      contrastText: "#ffffff",
    },

    secondary: {
      main: "#9c27b0",
      light: "#d05ce3",
      dark: "#6a0080",
      contrastText: "#ffffff",
    },

    error: {
      main: "#d32f2f",
    },

    warning: {
      main: "#ed6c02",
    },

    info: {
      main: "#0288d1",
    },

    success: {
      main: "#2e7d32",
    },

    background: {
      default: "#f5f5f5", // app background
      paper: "#ffffff",   // cards
    },

    text: {
      primary: "rgba(0, 0, 0, 0.87)",
      secondary: "rgba(0, 0, 0, 0.6)",
      disabled: "rgba(0, 0, 0, 0.38)",
    },

    divider: "rgba(0, 0, 0, 0.12)",

    action: {
      active: "rgba(0, 0, 0, 0.54)",
      hover: "rgba(0, 0, 0, 0.04)",
      selected: "rgba(0, 0, 0, 0.08)",
      disabled: "rgba(0, 0, 0, 0.26)",
      disabledBackground: "rgba(0, 0, 0, 0.12)",
      focus: "rgba(0, 0, 0, 0.12)",
    },
  },
});
