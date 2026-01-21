// frontend/src/App.tsx

// == Imports =====================================================================================
import { useState } from "react";
import { ThemeProvider } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import { Box } from "@mui/material";

import { darkTheme, lightTheme } from "./utils/theme";
import Header from "./components/generic/Header";
import LaTexEditor from "./components/editor/Editor";

// == Types & Constants ===========================================================================

// == Main Component ==============================================================================
export default function App() {
  // -- State Management --------------------------------------------------------------------------
  const [darkMode, setDarkMode] = useState(true);
  const [content, setContent] = useState<string>(
    "### My Header\n" +
      "Math works: $e^{i\\pi}-1=0$\n\n" +
      "Images work: ![Alt](https://via.placeholder.com/150)",
  );
  // -- Handlers / Callbacks ----------------------------------------------------------------------

  // -- Effect Management -------------------------------------------------------------------------

  // -- Function Constants ------------------------------------------------------------------------

  // -- Render ------------------------------------------------------------------------------------
  return (
    <ThemeProvider theme={darkMode ? darkTheme : lightTheme}>
      <CssBaseline />

      <Header darkMode={darkMode} onToggleTheme={setDarkMode} />

      <Box sx={{ p: 3 }}>
        <LaTexEditor content={content} setContent={setContent} />
      </Box>
    </ThemeProvider>
  );
}
