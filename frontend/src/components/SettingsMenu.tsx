import {
  Menu,
  MenuItem,
  Stack,
  Typography,
  Box,
  Divider,
  useTheme,
  ToggleButton,
  ToggleButtonGroup,
} from "@mui/material";
import {
  Palette as PaletteIcon,
  Logout as LogoutIcon,
  Person as PersonIcon,
  PersonAdd as PersonAddIcon,
  DarkMode as DarkModeIcon,
  LightMode as LightModeIcon,
} from "@mui/icons-material";
import { ThemeName, themeGroups, themeColors } from "../theme/themes";
import { useTheme as useAppTheme } from "../theme";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";

interface SettingsMenuProps {
  anchor: HTMLElement | null;
  onClose: () => void;
  onProfile: () => void;
  onLogout: () => void;
  themeName: ThemeName;
}

export const SettingsMenu = ({
  anchor,
  onClose,
  onProfile,
  onLogout,
  themeName: currentThemeName,
}: SettingsMenuProps) => {
  const theme = useTheme();
  const { user } = useAuth();
  const navigate = useNavigate();
  const { setThemeName } = useAppTheme();
  const isDark = currentThemeName.startsWith("dark");
  const availableThemes = isDark ? themeGroups.dark : themeGroups.light;
  const isGuestUser = Boolean(
    user &&
    (user.email.startsWith("guest+") || user.username.startsWith("guest_")),
  );

  const getThemeLabel = (name: ThemeName) => {
    const parts = name.split("-");
    return parts[1].charAt(0).toUpperCase() + parts[1].slice(1);
  };

  const currentMode = isDark ? "dark" : "light";

  const handleModeChange = (
    _event: React.MouseEvent<HTMLElement>,
    newMode: string | null,
  ) => {
    if (!newMode || newMode === currentMode) return;

    // Get the current theme style (e.g., "default" from "dark-default")
    const currentStyle = currentThemeName.split("-")[1];
    const potentialThemeName: ThemeName =
      `${newMode}-${currentStyle}` as ThemeName;

    // Check if the theme exists in the available themes for the new mode
    const themeModeGroup =
      newMode === "dark" ? themeGroups.dark : themeGroups.light;
    const newThemeName = themeModeGroup.includes(potentialThemeName)
      ? potentialThemeName
      : (themeModeGroup[0] as ThemeName); // Default to first theme of that mode

    setThemeName(newThemeName);
  };

  return (
    <Menu
      anchorEl={anchor}
      open={Boolean(anchor)}
      onClose={onClose}
      anchorOrigin={{
        vertical: "bottom",
        horizontal: "right",
      }}
      transformOrigin={{
        vertical: "top",
        horizontal: "right",
      }}
      PaperProps={{
        sx: {
          borderRadius: "12px",
          minWidth: "240px",
          background: `linear-gradient(135deg, ${theme.palette.background.paper} 0%, ${theme.palette.mode === "dark" ? "rgba(255, 255, 255, 0.05)" : "rgba(0, 0, 0, 0.02)"} 100%)`,
          backdropFilter: "blur(10px)",
        },
      }}
    >
      {/* Profile */}
      <MenuItem
        onClick={onProfile}
        sx={{
          gap: 1.5,
          py: 1.5,
        }}
      >
        <PersonIcon fontSize="small" />
        <Typography variant="body2">Profile</Typography>
      </MenuItem>

      <Divider sx={{ my: 0.5 }} />

      {/* Theme Selection */}
      <Box sx={{ px: 2, py: 1 }}>
        <Stack
          direction="row"
          spacing={1}
          sx={{ alignItems: "center", mb: 1, justifyContent: "space-between" }}
        >
          <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
            <PaletteIcon fontSize="small" sx={{ fontSize: "1rem" }} />
            <Typography
              variant="caption"
              sx={{
                fontWeight: 700,
                color: "text.secondary",
                fontSize: "0.75rem",
              }}
            >
              THEME
            </Typography>
          </Stack>

          <ToggleButtonGroup
            value={currentMode}
            exclusive
            onChange={handleModeChange}
            size="small"
            sx={{
              "& .MuiToggleButton-root": {
                border: "1px solid",
                borderColor: theme.palette.divider,
                padding: "4px 8px",
                "&.Mui-selected": {
                  backgroundColor: theme.palette.primary.main,
                  color: theme.palette.primary.contrastText,
                  borderColor: theme.palette.primary.main,
                  "&:hover": {
                    backgroundColor: theme.palette.primary.dark,
                  },
                },
              },
            }}
          >
            <ToggleButton value="light" aria-label="light mode">
              <LightModeIcon sx={{ fontSize: "1rem" }} />
            </ToggleButton>
            <ToggleButton value="dark" aria-label="dark mode">
              <DarkModeIcon sx={{ fontSize: "1rem" }} />
            </ToggleButton>
          </ToggleButtonGroup>
        </Stack>

        <Stack spacing={0.5}>
          {availableThemes.map((name) => (
            <Box
              key={name}
              onClick={() => {
                setThemeName(name);
                onClose();
              }}
              sx={{
                p: 1,
                borderRadius: "6px",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 1,
                backgroundColor:
                  currentThemeName === name
                    ? theme.palette.primary.main
                    : "transparent",
                color:
                  currentThemeName === name
                    ? theme.palette.primary.contrastText
                    : "text.primary",
                transition: "all 0.2s ease",
                "&:hover": {
                  backgroundColor:
                    currentThemeName === name
                      ? theme.palette.primary.main
                      : theme.palette.mode === "dark"
                        ? "rgba(255, 255, 255, 0.1)"
                        : "rgba(0, 0, 0, 0.05)",
                },
              }}
            >
              <Box
                sx={{
                  width: 16,
                  height: 16,
                  borderRadius: "4px",
                  background: `linear-gradient(135deg, ${themeColors[name].primary.main}, ${themeColors[name].secondary.main})`,
                }}
              />
              <Typography variant="body2" sx={{ fontSize: "0.875rem" }}>
                {getThemeLabel(name)}
              </Typography>
            </Box>
          ))}
        </Stack>
      </Box>

      <Divider sx={{ my: 0.5 }} />

      {isGuestUser && (
        <MenuItem
          onClick={() => {
            onClose();
            navigate("/auth/register");
          }}
          sx={{
            gap: 1.5,
            py: 1.5,
          }}
        >
          <PersonAddIcon fontSize="small" />
          <Typography variant="body2">Register</Typography>
        </MenuItem>
      )}

      {/* Logout */}
      <MenuItem
        onClick={onLogout}
        sx={{
          gap: 1.5,
          py: 1.5,
          color: theme.palette.error?.main || "#ff6b6b",
        }}
      >
        <LogoutIcon fontSize="small" />
        <Typography variant="body2">Logout</Typography>
      </MenuItem>
    </Menu>
  );
};
