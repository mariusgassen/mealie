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
