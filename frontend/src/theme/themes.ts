import { createTheme } from "@mui/material/styles";
import { ReactNode } from "react";

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
