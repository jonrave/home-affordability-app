import type { Scenario } from "./api";

const SCENARIO_STORAGE_KEY = "home-affordability:scenario";

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function mergeDefaults<T>(defaults: T, saved: unknown): T {
  if (!isRecord(defaults) || !isRecord(saved)) return defaults;
  const merged: Record<string, unknown> = { ...defaults };
  for (const [key, value] of Object.entries(saved)) {
    if (key in merged && isRecord(merged[key]) && isRecord(value)) {
      merged[key] = mergeDefaults(merged[key], value);
    } else {
      merged[key] = value;
    }
  }
  return merged as T;
}

export function loadStoredScenario(defaults: Scenario): Scenario {
  if (typeof window === "undefined") return structuredClone(defaults);
  try {
    const raw = window.localStorage.getItem(SCENARIO_STORAGE_KEY);
    if (!raw) return structuredClone(defaults);
    return mergeDefaults(structuredClone(defaults), JSON.parse(raw));
  } catch {
    return structuredClone(defaults);
  }
}

export function hasStoredScenario() {
  if (typeof window === "undefined") return false;
  try {
    return window.localStorage.getItem(SCENARIO_STORAGE_KEY) !== null;
  } catch {
    return false;
  }
}

export function saveStoredScenario(scenario: Scenario) {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(SCENARIO_STORAGE_KEY, JSON.stringify(scenario));
  } catch {
    // Storage can be unavailable in private or restricted browser contexts.
  }
}

export function clearStoredScenario() {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(SCENARIO_STORAGE_KEY);
  } catch {
    // Storage can be unavailable in private or restricted browser contexts.
  }
}
