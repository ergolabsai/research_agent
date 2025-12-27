import { createTheme, PaletteOptions } from "@mui/material/styles";

export type ThemeMode = "light" | "dark";

/* ----------------------------------
   Palette tokens (colors only)
---------------------------------- */
const lightPalette: PaletteOptions = {
  mode: "dark",

  primary: {
    light: "#e6ceceff",
    main: "#752f83ff",
    dark: "#000000",
    contrastText: "#FFFFFF",
  },

  secondary: {
    light: "#FFFFFF",
    main: "#9c27b0",
    dark: "#000000",
    contrastText: "#FFFFFF",
  },

  error: {
    light: "#FFFFFF",
    main: "#d32f2f",
    dark: "#000000",
    contrastText: "#FFFFFF",
  },

  warning: {
    light: "#FFFFFF",
    main: "#ed6c02",
    dark: "#000000",
    contrastText: "#000000",
  },

  info: {
    light: "#FFFFFF",
    main: "#0288d1",
    dark: "#000000",
    contrastText: "#FFFFFF",
  },

  success: {
    light: "#FFFFFF",
    main: "#2e7d32",
    dark: "#000000",
    contrastText: "#FFFFFF",
  },

  background: {
    default: "#dabfd5ff",
    paper: "#e7ccd9ff",
  },

  text: {
    primary: "#000000",
    secondary: "#000000",
    disabled: "#000000",
  },

  divider: "#000000",

  action: {
    active: "#000000",
    hover: "#000000",
    hoverOpacity: 0.08,
    selected: "#000000",
    selectedOpacity: 0.16,
    disabled: "#000000",
    disabledOpacity: 0.38,
    focus: "#000000",
    focusOpacity: 0.12,
    activatedOpacity: 0.24,
  },
};

const darkPalette: PaletteOptions = {
  mode: "dark",

  primary: {
    light: "#e6ceceff",
    main: "#752f83ff",
    dark: "#000000",
    contrastText: "#FFFFFF",
  },

  secondary: {
    light: "#FFFFFF",
    main: "#9c27b0",
    dark: "#000000",
    contrastText: "#FFFFFF",
  },

  error: {
    light: "#FFFFFF",
    main: "#d32f2f",
    dark: "#000000",
    contrastText: "#FFFFFF",
  },

  warning: {
    light: "#FFFFFF",
    main: "#ed6c02",
    dark: "#000000",
    contrastText: "#000000",
  },

  info: {
    light: "#FFFFFF",
    main: "#0288d1",
    dark: "#000000",
    contrastText: "#FFFFFF",
  },

  success: {
    light: "#FFFFFF",
    main: "#2e7d32",
    dark: "#000000",
    contrastText: "#FFFFFF",
  },

  background: {
    default: "#200b1cff",
    paper: "#501a34ff",
  },

  text: {
    primary: "#dbc3c3ff",
    secondary: "#000000",
    disabled: "#000000",
  },

  divider: "#000000",

  action: {
    active: "#000000",
    hover: "#000000",
    hoverOpacity: 0.08,
    selected: "#000000",
    selectedOpacity: 0.16,
    disabled: "#000000",
    disabledOpacity: 0.38,
    focus: "#000000",
    focusOpacity: 0.12,
    activatedOpacity: 0.24,
  },
};

/* ----------------------------------
   Theme factory
---------------------------------- */
export const getTheme = (mode: ThemeMode) =>
  createTheme({
    palette: mode === "dark" ? darkPalette : lightPalette,

    typography: {
      fontFamily: '"Inter", system-ui, sans-serif',
    },

    shape: {
      borderRadius: 8,
    },

    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: "none",
          },
        },
      },
    },
  });
