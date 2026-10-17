import { describe, expect, test } from "vitest";
import { isHexColor, THEME_COLORS } from "./use-theme-editor";
import { contrastRatio, generateTheme, hexToHsl, hslToHex, THEME_STYLES } from "./use-theme-generator";

/** Small deterministic generator so the tests do not depend on Math.random */
function seeded(seed: number) {
  let state = seed;
  return () => {
    state = (state + 0x6d2b79f5) | 0;
    let t = Math.imul(state ^ (state >>> 15), 1 | state);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

describe("hex <-> hsl", () => {
  test.each(["#E58325", "#2F8F7A", "#FFFFFF", "#000000", "#7E6BC4"])("round-trips %s", (hex) => {
    const back = hslToHex(hexToHsl(hex));
    expect(contrastRatio(hex, back)).toBeCloseTo(1, 1);
  });
});

describe("generateTheme", () => {
  test.each(THEME_STYLES)("%s: every role is a valid color in both modes", (style) => {
    for (let seed = 1; seed <= 25; seed++) {
      const theme = generateTheme({ style, random: seeded(seed) });
      for (const mode of ["light", "dark"] as const) {
        for (const color of THEME_COLORS) {
          expect(isHexColor(theme[mode][color])).toBe(true);
        }
      }
    }
  });

  test.each(THEME_STYLES)("%s: colored roles stay readable", (style) => {
    for (let seed = 1; seed <= 25; seed++) {
      const { light, dark } = generateTheme({ style, random: seeded(seed) });
      for (const color of ["primary", "accent", "secondary", "success", "info", "warning", "error"] as const) {
        expect(contrastRatio("#FFFFFF", light[color])).toBeGreaterThanOrEqual(3);
        expect(contrastRatio(dark.surface, dark[color])).toBeGreaterThanOrEqual(4.5);
      }
    }
  });

  test("dark backgrounds are dark and light backgrounds are light", () => {
    const { light, dark } = generateTheme({ style: "pastel", random: seeded(7) });
    expect(hexToHsl(light.background).l).toBeGreaterThan(90);
    expect(hexToHsl(dark.background).l).toBeLessThan(20);
  });

  test("keeps the chosen main color exactly for light mode", () => {
    const theme = generateTheme({ style: "vivid", baseColor: "#e58325", random: seeded(3) });
    expect(theme.light.primary).toBe("#E58325");
    // the dark main color keeps the hue
    expect(Math.abs(hexToHsl(theme.dark.primary).h - hexToHsl("#E58325").h)).toBeLessThan(6);
  });

  test("ignores an invalid base color and rolls a random one", () => {
    const theme = generateTheme({ style: "muted", baseColor: "nope", random: seeded(5) });
    expect(isHexColor(theme.light.primary)).toBe(true);
  });

  test("different seeds give different palettes, the same seed the same one", () => {
    const a = generateTheme({ style: "vivid", random: seeded(1) });
    const b = generateTheme({ style: "vivid", random: seeded(2) });
    expect(a.light.primary).not.toBe(b.light.primary);
    expect(generateTheme({ style: "vivid", random: seeded(1) })).toEqual(a);
  });

  test("pastel is less saturated than vivid for the same seed", () => {
    const vivid = generateTheme({ style: "vivid", random: seeded(9) });
    const pastel = generateTheme({ style: "pastel", random: seeded(9) });
    expect(hexToHsl(pastel.light.primary).s).toBeLessThan(hexToHsl(vivid.light.primary).s);
  });
});
