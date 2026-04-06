import type { SxProps, Theme } from "@mui/material";

/**
 * Returns an `sx`-compatible filter that inverts a light-background image
 * for dark mode (invert brightness, then hue-rotate to restore colours).
 * Returns an empty object in light mode so it can be spread unconditionally.
 */
export function darkModeImgSx(mode: "light" | "dark"): SxProps<Theme> {
  return mode === "dark" ? { filter: "invert(1) hue-rotate(180deg)" } : {};
}
