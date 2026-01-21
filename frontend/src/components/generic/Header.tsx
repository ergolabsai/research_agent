// frontend/src/components/generic/Header.tsx

// == Imports =====================================================================================
import { useState } from "react";
import {
  AppBar,
  Toolbar,
  IconButton,
  Menu,
  MenuItem,
  Switch,
  Box,
  Typography,
} from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import { MoreHoriz } from "@mui/icons-material";
import { ErgoSpinner } from "./ErgoSpinner";

// == Types & Constants ===========================================================================
interface HeaderProps {
  darkMode: boolean;
  onToggleTheme: (checked: boolean) => void;
}

// == Main Component ==============================================================================
export default function Header({ darkMode, onToggleTheme }: HeaderProps) {
  // -- State Management --------------------------------------------------------------------------
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);

  // -- Handlers / Callbacks ----------------------------------------------------------------------
  const handleMenuOpen = (e: React.MouseEvent<HTMLElement>) =>
    setAnchorEl(e.currentTarget);
  const handleMenuClose = () => setAnchorEl(null);
  const handleThemeToggle = (e: React.ChangeEvent<HTMLInputElement>) =>
    onToggleTheme(e.target.checked);

  // -- Effect Management -------------------------------------------------------------------------

  // -- Function Constants ------------------------------------------------------------------------

  // -- Render ------------------------------------------------------------------------------------
  return (
    <AppBar
      position="static"
      elevation={0}
      sx={{ bgcolor: "background.default" }}
    >
      <Toolbar variant="dense">
        {/* == Burger Menu ==*/}
        <IconButton edge="start" aria-label="menu" sx={{ mr: 2 }}>
          <MenuIcon />
        </IconButton>

        {/* == Center Placeholder ==*/}
        <Box
          sx={{
            flexGrow: 1,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 2,
          }}
        >
          <ErgoSpinner />
        </Box>

        {/* == Settings Menu ==*/}
        <IconButton
          onClick={handleMenuOpen}
          sx={{ backgroundColor: open ? "action.hover" : "transparent" }}
        >
          <MoreHoriz />
        </IconButton>

        <Menu
          anchorEl={anchorEl}
          open={open}
          onClose={handleMenuClose}
          anchorOrigin={{
            vertical: "bottom",
            horizontal: "right",
          }}
          transformOrigin={{
            vertical: "top",
            horizontal: "right",
          }}
          slotProps={{
            paper: {
              sx: {
                mt: 1,
                border: 1,
                borderColor: "divider",
              },
            },
          }}
        >
          <MenuItem
            sx={{ display: "flex", justifyContent: "space-between", gap: 2 }}
          >
            Dark Mode
            <Switch checked={darkMode} onChange={handleThemeToggle} />
          </MenuItem>
        </Menu>
      </Toolbar>
    </AppBar>
  );
}
