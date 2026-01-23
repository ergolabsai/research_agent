// frontend/src/App.tsx

// == Imports =====================================================================================
import { useEffect, useState } from "react";
import { ThemeProvider } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import {
  Box,
  Button,
  FormControl,
  FormHelperText,
  MenuItem,
  Select,
} from "@mui/material";

import { darkTheme, lightTheme } from "./utils/theme";
import Header from "./components/generic/Header";
import LaTexEditor from "./components/editor/Editor";
import axios from "axios";

// == Types & Constants ===========================================================================
const apiBase = "http://localhost:5173/api/db/docs";
const testContent =
  "### My Header\nMath works: $e^{i\\pi}-1=0$\n\nSome more text.";

// == Main Component ==============================================================================
export default function App() {
  // -- State Management --------------------------------------------------------------------------
  const [darkMode, setDarkMode] = useState(true);
  const [content, setContent] = useState<string>(testContent);
  const [docIds, setDocIds] = useState<number[]>([]);
  const [docId, setDocId] = useState<String>("1");

  // -- Handlers / Callbacks ----------------------------------------------------------------------
  const handleSaveAsNew = () => {
    axios
      .post(`${apiBase}/new`, { content })
      .then((res) => {
        const newId = res.data.id;
        setDocIds((prev) => [...prev, newId]);
        setDocId(String(newId));
      })
      .catch((err) => console.error("Error creating document:", err));
  };

  const handleSave = () => {
    axios
      .patch(`${apiBase}/${docId}`, { content })
      .catch((err) => console.error("Error updating document:", err));
  };

  const handleLoad = () => {
    axios
      .get(`${apiBase}/${docId}`)
      .then((res) => setContent(res.data.content))
      .catch((err) => console.error("Error loading document:", err));
  };

  const handleSetDocId = (event: any) => {
    setDocId(event.target.value);
  };

  // -- Effect Management -------------------------------------------------------------------------
  useEffect(() => {
    axios
      .get(`${apiBase}`)
      .then((res) => setDocIds(res.data.map((item: any) => item.id)))
      .catch((err) => console.error("Error loading document:", err));
  }, []);

  // -- Function Constants ------------------------------------------------------------------------

  // -- Render ------------------------------------------------------------------------------------
  return (
    <ThemeProvider theme={darkMode ? darkTheme : lightTheme}>
      <CssBaseline />

      <Header darkMode={darkMode} onToggleTheme={setDarkMode} />

      <Box sx={{ p: 3 }}>
        <LaTexEditor content={content} setContent={setContent} />

        <FormControl sx={{ m: 1, minWidth: 120 }}>
          <Select
            value={docId}
            onChange={handleSetDocId}
            sx={{ m: 1, mt: 0, mb: 0, height: 30 }}
          >
            {docIds.map((id) => {
              return <MenuItem value={id}>{id}</MenuItem>;
            })}
          </Select>
          <FormHelperText>Document ID</FormHelperText>
        </FormControl>
        <Button
          variant="contained"
          sx={{ m: 1, height: 30 }}
          onClick={handleLoad}
        >
          Load
        </Button>
        <Button
          variant="contained"
          sx={{ m: 1, height: 30 }}
          onClick={handleSave}
        >
          Save
        </Button>
        <Button
          variant="contained"
          sx={{ m: 1, height: 30 }}
          onClick={handleSaveAsNew}
        >
          Save As New
        </Button>
      </Box>
    </ThemeProvider>
  );
}
