// src/Settings.tsx
import { Box, Button, Typography } from "@mui/material";
import { ThemeMode } from "./theme";

type SettingsProps = {
  mode: ThemeMode;
  toggleTheme: () => void;
};

export default function Settings({ mode, toggleTheme }: SettingsProps) {
  return (
    <Box
      sx={{
        textAlign: "center",
        mt: 4,
      }}
    >
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>

      <Typography mb={2}>Current theme: {mode}</Typography>

      <Button variant="contained" onClick={toggleTheme}>
        Toggle Theme
      </Button>
    </Box>
  );
}
