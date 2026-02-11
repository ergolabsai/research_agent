import { ThemeProvider } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import GlobalStyles from "@mui/material/GlobalStyles";
import {
  ReactNode,
  useState,
  useEffect,
  createContext,
  useContext,
} from "react";
import { createAppTheme, ThemeName } from "./themes";

interface AppThemeProviderProps {
  children: ReactNode;
}

interface ThemeContextType {
  themeName: ThemeName;
  setThemeName: (name: ThemeName) => void;
}

export const ThemeContext = createContext<ThemeContextType | undefined>(
  undefined,
);

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within AppThemeProvider");
  }
  return context;
};

export const AppThemeProvider = ({ children }: AppThemeProviderProps) => {
  const [themeName, setThemeName] = useState<ThemeName>(() => {
    const saved = localStorage.getItem("theme");
    return (saved as ThemeName) || "dark-default";
  });

  useEffect(() => {
    localStorage.setItem("theme", themeName);
  }, [themeName]);

  const theme = createAppTheme(themeName);

  return (
    <ThemeProvider theme={theme}>
      <GlobalStyles
        styles={{
          "*": {
            scrollbarWidth: "thin",
            scrollbarColor: `${theme.palette.secondary.main}70 transparent`,
          },
          "*::-webkit-scrollbar": {
            width: "8px",
            height: "8px",
          },
          "*::-webkit-scrollbar-track": {
            background: "transparent",
          },
          "*::-webkit-scrollbar-thumb": {
            background: theme.palette.primary.main,
            borderRadius: "4px",
          },
          "*::-webkit-scrollbar-thumb:hover": {
            background: theme.palette.primary.dark,
          },
        }}
      />
      <CssBaseline />
      <ThemeContext.Provider value={{ themeName, setThemeName }}>
        {children}
      </ThemeContext.Provider>
    </ThemeProvider>
  );
};
