import { describe, expect, test } from "vitest";
import type { RecipeIngredient, RecipeStep } from "~/lib/api/types/recipe";
import { ingredientsForStep } from "./use-cook-step-ingredients";

const food = (id: string, name: string, extra: Partial<NonNullable<RecipeIngredient["food"]>> = {}) => ({ id, name, ...extra });
const ingredient = (referenceId: string, name: string, extra: Partial<RecipeIngredient["food"] & object> = {}): RecipeIngredient => ({
  referenceId,
  quantity: 1,
  food: food(referenceId, name, extra),
});
const step = (text: string, refs: string[] = [], summary = ""): RecipeStep => ({
  id: "s",
  summary,
  text,
  ingredientReferences: refs.map(referenceId => ({ referenceId })),
});

const chicken = ingredient("i1", "chicken thigh", { pluralName: "chicken thighs" });
const chipotle = ingredient("i2", "chipotle in adobo");
const oil = ingredient("i3", "olive oil");
const tortilla = ingredient("i4", "corn tortilla", { pluralName: "corn tortillas" });
const salt = ingredient("i5", "salt");
const all = [chicken, chipotle, oil, tortilla, salt];

describe("ingredientsForStep", () => {
  test("no step yields nothing", () => {
    expect(ingredientsForStep(all, undefined)).toEqual({ ingredients: [], source: "none" });
  });

  test("linked references win and keep the step's order", () => {
    const result = ingredientsForStep(all, step("Mix everything with the chicken.", ["i3", "i1"]));
    expect(result.source).toBe("linked");
    expect(result.ingredients).toEqual([oil, chicken]);
  });

  test("unknown and duplicate references are ignored", () => {
    const result = ingredientsForStep(all, step("Cook.", ["nope", "i1", "i1"]));
    expect(result.source).toBe("linked");
    expect(result.ingredients).toEqual([chicken]);
  });

  test("falls back to matching when every reference is unknown", () => {
    const result = ingredientsForStep(all, step("Season the chicken thighs.", ["nope"]));
    expect(result.source).toBe("matched");
    expect(result.ingredients).toEqual([chicken]);
  });

  test("matches by food name, plural name and singular/plural text", () => {
    expect(ingredientsForStep(all, step("Warm the corn tortillas.")).ingredients).toEqual([tortilla]);
    expect(ingredientsForStep(all, step("Warm the tortilla in a pan.")).ingredients).toEqual([tortilla]);
  });

  test("matches an alias", () => {
    const withAlias = [ingredient("i9", "coriander", { aliases: [{ name: "cilantro" }] })];
    expect(ingredientsForStep(withAlias, step("Top with cilantro.")).ingredients).toEqual(withAlias);
  });

  test("matches a longer food name by one distinctive word", () => {
    const result = ingredientsForStep(all, step("Stir in the chipotle and cook for a minute."));
    expect(result.source).toBe("matched");
    expect(result.ingredients).toEqual([chipotle]);
  });

  test("does not match on generic words", () => {
    const sweetPotato = [ingredient("i7", "sweet potato")];
    expect(ingredientsForStep(sweetPotato, step("Add something sweet.")).source).toBe("none");
  });

  test("does not match inside other words", () => {
    // "salt" must not match "Basalt"
    expect(ingredientsForStep([salt], step("Place on the basalt slab.")).source).toBe("none");
  });

  test("uses the summary as well as the text, in ingredient order", () => {
    const result = ingredientsForStep(all, step("Heat the pan.", [], "Add the olive oil and chicken"));
    expect(result.ingredients).toEqual([chicken, oil]);
  });

  test("reports none when nothing is recognised", () => {
    expect(ingredientsForStep(all, step("Let it rest for five minutes.")).source).toBe("none");
  });

  test("free-text ingredients without a food match on their note", () => {
    const freeText: RecipeIngredient = { referenceId: "i8", note: "a pinch of saffron" };
    const result = ingredientsForStep([freeText], step("Bloom the saffron."));
    expect(result.source).toBe("matched");
  });
});
