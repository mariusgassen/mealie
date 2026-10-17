import type { AppTheme, AppThemeUpdate } from "~/lib/api/types/admin";

export const THEME_COLORS = [
  "primary",
  "accent",
  "secondary",
  "success",
  "info",
  "warning",
  "error",
  "background",
  "surface",
] as const;

export type ThemeColor = (typeof THEME_COLORS)[number];
export type ThemeMode = "light" | "dark";

export const THEME_MODES: ThemeMode[] = ["light", "dark"];

/** The AppTheme field for one color of one mode, e.g. ("dark", "primary") -> "darkPrimary" */
export function themeKey(mode: ThemeMode, color: ThemeColor): keyof AppTheme {
  return `${mode}${color.charAt(0).toUpperCase()}${color.slice(1)}` as keyof AppTheme;
}

const HEX_COLOR = /^#[0-9A-F]{6}$/;

export function isHexColor(value: string | null | undefined): value is string {
  return !!value && HEX_COLOR.test(value.toUpperCase());
}

/** Accepts what people type ("e58325", " #e58325 ") and returns "#E58325", or null if it is not a 6-digit hex color. */
export function normalizeHexColor(value: string): string | null {
  const trimmed = value.trim().toUpperCase();
  const withHash = trimmed.startsWith("#") ? trimmed : `#${trimmed}`;
  return HEX_COLOR.test(withHash) ? withHash : null;
}

/**
 * The partial update to send so the server ends up with `draft`.
 *
 * Only values that differ from what is saved are included. A value equal to the default is sent as
 * `null`, which removes the admin override instead of pinning the default in the database, so a later
 * change of the environment variables or built-in defaults still takes effect.
 */
export function buildThemeUpdate(draft: AppTheme, saved: AppTheme, defaults: AppTheme): AppThemeUpdate {
  const update: Record<string, string | null> = {};

  for (const mode of THEME_MODES) {
    for (const color of THEME_COLORS) {
      const key = themeKey(mode, color);
      const next = draft[key];
      if (next === saved[key]) {
        continue;
      }
      update[key] = !next || next === defaults[key] ? null : next;
    }
  }

  return update as AppThemeUpdate;
}

/** Black or white, whichever is easier to read on `background` (WCAG relative luminance). */
export function readableTextColor(background: string): "#000000" | "#FFFFFF" {
  const hex = normalizeHexColor(background);
  if (!hex) {
    return "#000000";
  }

  const [r, g, b] = [1, 3, 5].map((start) => {
    const channel = parseInt(hex.slice(start, start + 2), 16) / 255;
    return channel <= 0.03928 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
  }) as [number, number, number];

  const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b;
  // white text wins when the background is darker than the luminance where both have equal contrast (~0.179)
  return luminance > 0.179 ? "#000000" : "#FFFFFF";
}

type ThemePalette = Record<ThemeColor, string>;

/** Ready-made palettes that fill every color of both modes at once; the admin still has to save them. */
export const THEME_PRESETS: Record<string, { light: ThemePalette; dark: ThemePalette }> = {
  sage: {
    light: {
      primary: "#2F8F7A",
      accent: "#D77C56",
      secondary: "#7E6BC4",
      success: "#4E9F77",
      info: "#4C8FD0",
      warning: "#C2822A",
      error: "#D1606A",
      background: "#F4F8F6",
      surface: "#FFFFFF",
    },
    dark: {
      primary: "#8ED1B8",
      accent: "#F5B896",
      secondary: "#B7A8F0",
      success: "#93D5B2",
      info: "#96C4F0",
      warning: "#F5CB8C",
      error: "#F29B9B",
      background: "#1E2523",
      surface: "#29322F",
    },
  },
};

/** `theme` with every color of `preset` applied, for light and dark alike. */
export function applyThemePreset(theme: AppTheme, preset: string): AppTheme {
  const next = { ...theme };

  for (const mode of THEME_MODES) {
    for (const color of THEME_COLORS) {
      (next as Record<string, string>)[themeKey(mode, color)] = THEME_PRESETS[preset]![mode][color];
    }
  }

  return next;
}
