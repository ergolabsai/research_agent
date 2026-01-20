// frontend/src/App.tsx

// == Imports =====================================================================================
import { useState } from "react";
import { ThemeProvider } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import { Box } from "@mui/material";

import { darkTheme, lightTheme } from "./utils/theme";
import Header from "./components/generic/Header";

// == Types & Constants ===========================================================================

// == Main Component ==============================================================================
export default function App() {
  // -- State Management --------------------------------------------------------------------------
  const [darkMode, setDarkMode] = useState(true);

  // -- Handlers / Callbacks ----------------------------------------------------------------------

  // -- Effect Management -------------------------------------------------------------------------

  // -- Function Constants ------------------------------------------------------------------------

  // -- Render ------------------------------------------------------------------------------------
  return (
    <ThemeProvider theme={darkMode ? darkTheme : lightTheme}>
      <CssBaseline />

      <Header darkMode={darkMode} onToggleTheme={setDarkMode} />

      <Box sx={{ p: 3 }}>Page content goes here okay.</Box>
    </ThemeProvider>
  );
}
