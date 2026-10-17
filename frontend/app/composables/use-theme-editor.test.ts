import { describe, expect, test } from "vitest";
import type { AppTheme } from "~/lib/api/types/admin";
import {
  applyThemePreset,
  buildThemeUpdate,
  isHexColor,
  normalizeHexColor,
  readableTextColor,
  themeKey,
  THEME_COLORS,
  THEME_MODES,
  THEME_PRESETS,
} from "./use-theme-editor";
import { contrastRatio } from "./use-theme-generator";

const defaults: AppTheme = {
  lightPrimary: "#E58325",
  lightBackground: "#F2F2F7",
  darkPrimary: "#E58325",
  darkSurface: "#2C2C2E",
};

describe("themeKey", () => {
  test("builds the AppTheme field name", () => {
    expect(themeKey("dark", "primary")).toBe("darkPrimary");
    expect(themeKey("light", "background")).toBe("lightBackground");
  });
});

describe("normalizeHexColor", () => {
  test.each([
    ["#e58325", "#E58325"],
    ["e58325", "#E58325"],
    ["  #abCDef ", "#ABCDEF"],
  ])("accepts %s", (input, expected) => {
    expect(normalizeHexColor(input)).toBe(expected);
  });

  test.each(["", "#fff", "red", "#12345G", "#1234567", "rgb(1,2,3)"])("rejects %j", (input) => {
    expect(normalizeHexColor(input)).toBeNull();
  });
});

describe("isHexColor", () => {
  test("only full 6-digit colors are valid", () => {
    expect(isHexColor("#E58325")).toBe(true);
    expect(isHexColor("#e58325")).toBe(true);
    expect(isHexColor("#E58")).toBe(false);
    expect(isHexColor("")).toBe(false);
    expect(isHexColor(undefined)).toBe(false);
  });
});

describe("buildThemeUpdate", () => {
  test("sends nothing when nothing changed", () => {
    expect(buildThemeUpdate({ ...defaults }, { ...defaults }, defaults)).toEqual({});
  });

  test("sends only the colors that changed", () => {
    const saved = { ...defaults };
    const draft = { ...defaults, darkPrimary: "#112233" };
    expect(buildThemeUpdate(draft, saved, defaults)).toEqual({ darkPrimary: "#112233" });
  });

  test("a color changed back to its default clears the override", () => {
    const saved = { ...defaults, darkPrimary: "#112233" };
    const draft = { ...defaults };
    expect(buildThemeUpdate(draft, saved, defaults)).toEqual({ darkPrimary: null });
  });

  test("changing one override to another sends the new value", () => {
    const saved = { ...defaults, lightPrimary: "#111111" };
    const draft = { ...defaults, lightPrimary: "#222222" };
    expect(buildThemeUpdate(draft, saved, defaults)).toEqual({ lightPrimary: "#222222" });
  });

  test("handles several colors across both modes at once", () => {
    const saved = { ...defaults, darkSurface: "#000000" };
    const draft = { ...defaults, lightBackground: "#FFFFFF", darkSurface: defaults.darkSurface };
    expect(buildThemeUpdate(draft, saved, defaults)).toEqual({ lightBackground: "#FFFFFF", darkSurface: null });
  });

  test("a cleared value is sent as null", () => {
    const saved = { ...defaults, darkPrimary: "#112233" };
    expect(buildThemeUpdate({ ...saved, darkPrimary: "" }, saved, defaults)).toEqual({ darkPrimary: null });
  });
});

describe("readableTextColor", () => {
  test("dark backgrounds get white text, light ones black", () => {
    expect(readableTextColor("#000000")).toBe("#FFFFFF");
    expect(readableTextColor("#1C1C1E")).toBe("#FFFFFF");
    expect(readableTextColor("#FFFFFF")).toBe("#000000");
    expect(readableTextColor("#F2F2F7")).toBe("#000000");
  });

  test("mid-tones pick the higher-contrast side", () => {
    // the brand orange reads better with black text, a deep blue with white
    expect(readableTextColor("#E58325")).toBe("#000000");
    expect(readableTextColor("#1565C0")).toBe("#FFFFFF");
  });

  test("falls back to black for anything that is not a color", () => {
    expect(readableTextColor("not-a-color")).toBe("#000000");
  });
});

describe("theme presets", () => {
  test("every preset defines every color of both modes as a valid hex color", () => {
    for (const preset of Object.values(THEME_PRESETS)) {
      for (const mode of THEME_MODES) {
        for (const color of THEME_COLORS) {
          expect(isHexColor(preset[mode][color])).toBe(true);
        }
      }
    }
  });

  test("applyThemePreset fills light and dark and leaves the input untouched", () => {
    const before: AppTheme = { lightPrimary: "#111111", darkPrimary: "#222222" };
    const after = applyThemePreset(before, "sage");

    expect(after.lightPrimary).toBe(THEME_PRESETS.sage!.light.primary);
    expect(after.darkPrimary).toBe(THEME_PRESETS.sage!.dark.primary);
    expect(after.lightBackground).toBe(THEME_PRESETS.sage!.light.background);
    expect(before.lightPrimary).toBe("#111111");
  });
});

describe("built-in presets are readable", () => {
  const roles = ["primary", "accent", "secondary", "success", "info", "warning", "error"] as const;

  test.each(Object.keys(THEME_PRESETS))("%s: colored roles stand out from the surface in both modes", (name) => {
    const preset = THEME_PRESETS[name]!;
    for (const role of roles) {
      // colored text and icons on cards need at least 3:1 (large-text / UI-component level)
      expect(contrastRatio(preset.light[role], preset.light.surface), `light ${role}`).toBeGreaterThanOrEqual(3);
      expect(contrastRatio(preset.dark[role], preset.dark.surface), `dark ${role}`).toBeGreaterThanOrEqual(4.5);
    }
  });

  test.each(Object.keys(THEME_PRESETS))("%s: the app bar text is readable on the main color", (name) => {
    const preset = THEME_PRESETS[name]!;
    for (const mode of ["light", "dark"] as const) {
      const text = readableTextColor(preset[mode].primary);
      expect(contrastRatio(text, preset[mode].primary), mode).toBeGreaterThanOrEqual(4.5);
    }
  });

  test.each(Object.keys(THEME_PRESETS))("%s: cards are distinguishable from the page", (name) => {
    const preset = THEME_PRESETS[name]!;
    for (const mode of ["light", "dark"] as const) {
      expect(contrastRatio(preset[mode].surface, preset[mode].background), mode).toBeGreaterThan(1.03);
    }
  });
});
