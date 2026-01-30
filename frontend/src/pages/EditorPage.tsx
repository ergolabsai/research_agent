import { useParams } from "react-router-dom";
import {
  Box,
  TextField,
  useTheme,
  Stack,
  Button,
  Typography,
} from "@mui/material";
import { useState, useEffect } from "react";
import { documentsAPI } from "../api";
import {
  Functions as MathIcon,
  Psychology as LogicIcon,
  LineStyle as FormatterIcon,
  LocalLibrary as LibrarianIcon,
  Insights as PlotsIcon,
} from "@mui/icons-material";

export const EditorPage = () => {
  const { id } = useParams();
  const theme = useTheme();
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [hoveredIcon, setHoveredIcon] = useState<string | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    const loadDocument = async () => {
      if (!id) return;
      try {
        const response = await documentsAPI.get(Number(id));
        setContent(response.data.content || "");
        setTitle(response.data.title || "");
        setIsLoaded(true);
      } catch (err) {
        console.error("Failed to load document:", err);
        setIsLoaded(true);
      }
    };

    loadDocument();
  }, [id]);

  useEffect(() => {
    if (!isLoaded) return;

    const loadDocument = async () => {
      if (!id) return;
      try {
        await documentsAPI.update(Number(id), title, content);
      } catch (err) {
        console.error("Failed to load document:", err);
      }
    };

    loadDocument();
  }, [content, title, isLoaded]);

  const handleMath = () => {};
  const handleLogic = () => {};
  const handleFormatter = () => {};
  const handleLibrarian = () => {};
  const handlePlots = () => {};

  const buttons = [
    { id: "math", label: "Math", icon: MathIcon, handler: handleMath },
    { id: "logic", label: "Logic", icon: LogicIcon, handler: handleLogic },
    {
      id: "formatter",
      label: "Format",
      icon: FormatterIcon,
      handler: handleFormatter,
    },
    {
      id: "librarian",
      label: "Library",
      icon: LibrarianIcon,
      handler: handleLibrarian,
    },
    { id: "plots", label: "Plots", icon: PlotsIcon, handler: handlePlots },
  ];

  const buttonVariant = "contained";
  const buttonSx = {
    height: "56px",
    minWidth: "56px",
    padding: "0px",
    gap: "0px",
    display: "flex",
    flexDirection: "column" as const,
    alignItems: "center",
    justifyContent: "center",
    background: `linear-gradient(135deg, ${theme.palette.primary.main}BB 20%, ${theme.palette.secondary.main}BB 100%)`,
    transition: "transform 0.2s ease, box-shadow 0.2s ease",
    "&:hover": {
      transform: "translateY(-2px)",
      boxShadow: "0 8px 16px rgba(0, 0, 0, 0.15)",
    },
  };

  return (
    <Box
      sx={{
        height: "calc(100vh - 100px)",
        display: "flex",
        flexDirection: "column",
        gap: 2,
      }}
    >
      <Stack direction="row" sx={{ gap: 2, alignItems: "center" }}>
        <Box
          sx={{
            flex: 1,
            background: `linear-gradient(135deg, ${theme.palette.primary.main}10 0%, ${theme.palette.secondary.main}20 100%)`,
            borderRadius: "12px",
            border: "1px solid " + theme.palette.divider,
          }}
        >
          <TextField
            placeholder="Document Title"
            fullWidth
            size="small"
            sx={{
              height: "56px",
              display: "flex",
              alignItems: "center",
              "& .MuiInputBase-root": {
                height: "100%",
                fontSize: "1.5rem",
                fontWeight: 600,
              },
              "& .MuiOutlinedInput-root": { "& fieldset": { border: "none" } },
            }}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </Box>
        <Stack direction="row" sx={{ gap: 1 }}>
          {buttons.map((btn) => {
            const IconComponent = btn.icon;
            return (
              <Box
                key={btn.id}
                onMouseEnter={() => setHoveredIcon(btn.id)}
                onMouseLeave={() => setHoveredIcon(null)}
              >
                <Button
                  onClick={btn.handler}
                  variant={buttonVariant}
                  sx={{ ...buttonSx, position: "relative" }}
                >
                  <Box
                    sx={{
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                      justifyContent: "center",
                      width: "100%",
                      height: "100%",
                    }}
                  >
                    <IconComponent fontSize="small" />
                  </Box>
                  {hoveredIcon === btn.id && (
                    <Typography
                      variant="caption"
                      fontWeight={850}
                      sx={{
                        position: "absolute",
                        top: "5px",
                        fontSize: "0.65rem",
                        color: "background.default",
                        lineHeight: 1,
                        whiteSpace: "nowrap",
                      }}
                    >
                      {btn.label}
                    </Typography>
                  )}
                </Button>
              </Box>
            );
          })}
        </Stack>
      </Stack>
      <Box
        sx={{
          flex: 1,
          backgroundColor: theme.palette.background.paper,
          borderRadius: "12px",
          p: 2,
          border: "1px solid" + theme.palette.divider,
        }}
      >
        <TextField
          placeholder="Start writing your document..."
          variant="standard"
          fullWidth
          multiline
          minRows={10}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          sx={{ mt: 0 }}
        />
      </Box>
    </Box>
  );
};
