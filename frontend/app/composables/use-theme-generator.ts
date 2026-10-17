import { normalizeHexColor, type ThemeColor, type ThemeMode } from "~/composables/use-theme-editor";

export type ThemePalette = Record<ThemeColor, string>;
export type GeneratedTheme = Record<ThemeMode, ThemePalette>;

export const THEME_STYLES = ["vivid", "pastel", "muted", "deep"] as const;
export type ThemeStyle = (typeof THEME_STYLES)[number];

const HARMONIES = ["analogous", "complementary", "triad"] as const;
type Harmony = (typeof HARMONIES)[number];

/** Hue offsets (degrees) from the main color for the accent and secondary color */
const HARMONY_OFFSETS: Record<Harmony, [number, number]> = {
  analogous: [30, -30],
  complementary: [180, 30],
  triad: [120, 240],
};

/** Saturation / lightness (percent) for the colored roles, per style and mode */
const STYLE_LEVELS: Record<ThemeStyle, Record<ThemeMode, { s: number; l: number }>> = {
  vivid: { light: { s: 72, l: 42 }, dark: { s: 85, l: 66 } },
  pastel: { light: { s: 42, l: 42 }, dark: { s: 52, l: 76 } },
  muted: { light: { s: 24, l: 40 }, dark: { s: 28, l: 68 } },
  deep: { light: { s: 55, l: 30 }, dark: { s: 62, l: 62 } },
};

/** Saturation of the tinted page background, per style */
const BACKGROUND_SATURATION: Record<ThemeStyle, number> = { vivid: 30, pastel: 34, muted: 12, deep: 18 };

/** Hues of the status colors; they stay recognisable whatever the main color is */
const STATUS_HUES = { success: 145, info: 210, warning: 38, error: 355 } as const;

const MIN_CONTRAST_LIGHT = 3; // white text on a colored button
const MIN_CONTRAST_DARK = 4.5; // colored text on the dark surface

type Hsl = { h: number; s: number; l: number };

export function hexToHsl(hex: string): Hsl {
  const value = normalizeHexColor(hex) ?? "#000000";
  const [r, g, b] = [1, 3, 5].map(start => parseInt(value.slice(start, start + 2), 16) / 255) as [number, number, number];
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  const l = (max + min) / 2;
  const delta = max - min;

  if (delta === 0) {
    return { h: 0, s: 0, l: l * 100 };
  }

  const s = delta / (1 - Math.abs(2 * l - 1));
  let h: number;
  if (max === r) {
    h = ((g - b) / delta) % 6;
  }
  else if (max === g) {
    h = (b - r) / delta + 2;
  }
  else {
    h = (r - g) / delta + 4;
  }

  return { h: (h * 60 + 360) % 360, s: s * 100, l: l * 100 };
}

export function hslToHex({ h, s, l }: Hsl): string {
  const hue = ((h % 360) + 360) % 360;
  const sat = Math.min(Math.max(s, 0), 100) / 100;
  const light = Math.min(Math.max(l, 0), 100) / 100;
  const chroma = (1 - Math.abs(2 * light - 1)) * sat;
  const x = chroma * (1 - Math.abs(((hue / 60) % 2) - 1));
  const m = light - chroma / 2;

  const [r, g, b] = (
    [
      [chroma, x, 0],
      [x, chroma, 0],
      [0, chroma, x],
      [0, x, chroma],
      [x, 0, chroma],
      [chroma, 0, x],
    ] as const
  )[Math.floor(hue / 60) % 6]!;

  return `#${[r, g, b]
    .map(channel => Math.round((channel + m) * 255).toString(16).padStart(2, "0"))
    .join("")
    .toUpperCase()}`;
}

function luminance(hex: string): number {
  const value = normalizeHexColor(hex) ?? "#000000";
  const [r, g, b] = [1, 3, 5].map((start) => {
    const channel = parseInt(value.slice(start, start + 2), 16) / 255;
    return channel <= 0.03928 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
  }) as [number, number, number];

  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

/** WCAG contrast ratio between two colors, 1 (identical) to 21 (black on white) */
export function contrastRatio(a: string, b: string): number {
  const [lighter, darker] = [luminance(a), luminance(b)].sort((x, y) => y - x) as [number, number];
  return (lighter + 0.05) / (darker + 0.05);
}

/** Moves lightness in `direction` until `color` reaches `minimum` contrast against `against` */
function ensureContrast(color: Hsl, against: string, minimum: number, direction: 1 | -1): string {
  const adjusted = { ...color };
  while (contrastRatio(hslToHex(adjusted), against) < minimum && adjusted.l > 0 && adjusted.l < 100) {
    adjusted.l += direction;
  }
  return hslToHex(adjusted);
}

export interface GenerateOptions {
  style: ThemeStyle;
  /** Keep this exact color as the light main color and build the rest around it; random when omitted */
  baseColor?: string;
  /** Source of randomness (0 <= n < 1); `Math.random` by default, injectable for tests */
  random?: () => number;
}

/** A complete light and dark palette: a main color, two companions, status colors and tinted backgrounds. */
export function generateTheme({ style, baseColor, random = Math.random }: GenerateOptions): GeneratedTheme {
  const base = baseColor && normalizeHexColor(baseColor) ? hexToHsl(baseColor) : null;
  const hue = base ? base.h : random() * 360;
  const harmony = HARMONIES[Math.floor(random() * HARMONIES.length)]!;
  const [accentOffset, secondaryOffset] = HARMONY_OFFSETS[harmony];
  // a little jitter so repeated rolls with the same inputs still differ
  const jitter = () => (random() - 0.5) * 8;

  const palettes = {} as GeneratedTheme;

  for (const mode of ["light", "dark"] as const) {
    const { s, l } = STYLE_LEVELS[style][mode];
    const dark = mode === "dark";
    const surface = dark ? hslToHex({ h: hue, s: BACKGROUND_SATURATION[style] * 0.6, l: 16 }) : "#FFFFFF";
    const contrastAgainst = dark ? surface : "#FFFFFF";
    const minimum = dark ? MIN_CONTRAST_DARK : MIN_CONTRAST_LIGHT;
    const direction = dark ? 1 : -1;
    const colored = (h: number, lightnessShift = 0) =>
      ensureContrast({ h, s, l: l + lightnessShift + jitter() / 2 }, contrastAgainst, minimum, direction);

    let primary = colored(hue);
    if (base && !dark) {
      primary = normalizeHexColor(baseColor!)!;
    }
    else if (base && dark) {
      // same hue and saturation as the chosen color, lightened to read on the dark surface
      primary = ensureContrast({ h: base.h, s: Math.min(base.s, s + 10), l }, surface, minimum, 1);
    }

    palettes[mode] = {
      primary,
      accent: colored(hue + accentOffset),
      secondary: colored(hue + secondaryOffset),
      success: colored(STATUS_HUES.success),
      info: colored(STATUS_HUES.info),
      // yellow-orange needs more lightness to look like itself
      warning: colored(STATUS_HUES.warning, dark ? 0 : 6),
      error: colored(STATUS_HUES.error),
      background: hslToHex({ h: hue, s: dark ? BACKGROUND_SATURATION[style] * 0.55 : BACKGROUND_SATURATION[style], l: dark ? 11 : 96.5 }),
      surface,
    };
  }

  return palettes;
}
