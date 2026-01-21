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
} from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import { MoreHoriz } from "@mui/icons-material";

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
        <Box sx={{ flexGrow: 1 }} />

        {/* == Settings Menu ==*/}
        <IconButton onClick={handleMenuOpen}>
          <MoreHoriz />
        </IconButton>

        <Menu anchorEl={anchorEl} open={open} onClose={handleMenuClose}>
          <MenuItem>
            Dark Mode
            <Switch checked={darkMode} onChange={handleThemeToggle} />
          </MenuItem>
        </Menu>
      </Toolbar>
    </AppBar>
  );
}
