// src/main.tsx

import React, { useMemo, useState } from "react";
import { BrowserRouter } from "react-router-dom";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

import { ThemeProvider, CssBaseline } from "@mui/material";
import { getTheme, ThemeMode } from "./theme";

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Root element not found");
}

function Root() {
  const [mode, setMode] = useState<ThemeMode>("dark");

  const theme = useMemo(() => getTheme(mode), [mode]);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <App
          mode={mode}
          toggleTheme={() =>
            setMode((prev) => (prev === "light" ? "dark" : "light"))
          }
        />
      </BrowserRouter>
    </ThemeProvider>
  );
}

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>
);
