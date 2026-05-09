import type { Scenario } from "./api";

export function getScenarioPath<T = unknown>(source: Scenario, path: string[]): T {
  return path.reduce<any>((value, key) => value?.[key], source) as T;
}

export function getScenarioValue(source: Scenario, path: string[]): number {
  return getScenarioPath<number>(source, path);
}

export function setScenarioPath<T>(source: Scenario, path: string[], value: T): Scenario {
  const next = structuredClone(source);
  let cursor = next;
  for (const key of path.slice(0, -1)) {
    cursor = cursor[key];
  }
  cursor[path[path.length - 1]] = value;
  return next;
}

export function setScenarioValue(source: Scenario, path: string[], value: number): Scenario {
  return setScenarioPath(source, path, value);
}
