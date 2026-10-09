import type { RecipeIngredient, RecipeStep } from "~/lib/api/types/recipe";

/**
 * Which ingredients (and amounts) belong to a step, for cooking mode.
 *
 * - "linked":  the step explicitly links ingredients (ingredientReferences)
 * - "matched": nothing is linked, so ingredients are guessed from the step text
 * - "none":    nothing linked and nothing recognised in the text
 */
export type StepIngredientSource = "linked" | "matched" | "none";

export interface StepIngredients {
  ingredients: RecipeIngredient[];
  source: StepIngredientSource;
}

// words too generic to identify an ingredient on their own
const GENERIC_WORDS = new Set([
  "fresh", "dried", "ground", "whole", "large", "small", "sweet", "black", "white", "green",
  "hot", "cold", "warm", "light", "dark", "extra", "plain", "mixed", "chopped", "sliced",
]);

const MIN_WORD_LENGTH = 4;

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/** Lower-cased names a recipe step might use for this ingredient. */
function candidateNames(ingredient: RecipeIngredient): string[] {
  const food = ingredient.food;
  const names: (string | null | undefined)[] = food
    ? [food.name, food.pluralName, ...(food.aliases ?? []).map(alias => alias.name)]
    : [ingredient.note];

  return names
    .map(name => name?.trim().toLowerCase())
    .filter((name): name is string => !!name && name.length >= MIN_WORD_LENGTH - 1);
}

/** True when `word` starts a word in `text` (prefix match, so "tortilla" finds "tortillas"). */
function textMentions(text: string, word: string): boolean {
  return new RegExp(`(^|[^\\p{L}])${escapeRegExp(word)}`, "u").test(text);
}

function ingredientMentioned(text: string, ingredient: RecipeIngredient): boolean {
  return candidateNames(ingredient).some((name) => {
    if (textMentions(text, name)) {
      return true;
    }
    // "chipotle in adobo" is usually written "chipotle" in the method
    return name
      .split(/[^\p{L}]+/u)
      .filter(word => word.length >= MIN_WORD_LENGTH + 1 && !GENERIC_WORDS.has(word))
      .some(word => textMentions(text, word));
  });
}

export function ingredientsForStep(ingredients: RecipeIngredient[], step: RecipeStep | undefined): StepIngredients {
  if (!step) {
    return { ingredients: [], source: "none" };
  }

  const byReference = new Map<string, RecipeIngredient>();
  ingredients.forEach((ingredient) => {
    if (ingredient.referenceId) {
      byReference.set(ingredient.referenceId, ingredient);
    }
  });

  const linked: RecipeIngredient[] = [];
  (step.ingredientReferences ?? []).forEach((reference) => {
    const ingredient = reference.referenceId ? byReference.get(reference.referenceId) : undefined;
    if (ingredient && !linked.includes(ingredient)) {
      linked.push(ingredient);
    }
  });
  if (linked.length > 0) {
    return { ingredients: linked, source: "linked" };
  }

  const text = `${step.summary ?? ""} ${step.text ?? ""}`.toLowerCase();
  if (!text.trim()) {
    return { ingredients: [], source: "none" };
  }

  const matched = ingredients.filter(ingredient => ingredientMentioned(text, ingredient));
  return { ingredients: matched, source: matched.length > 0 ? "matched" : "none" };
}
