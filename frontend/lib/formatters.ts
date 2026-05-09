export const currency = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0
});

export const preciseCurrency = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 2
});

export const number = new Intl.NumberFormat("en-US", {
  maximumFractionDigits: 1
});

export const percent = new Intl.NumberFormat("en-US", {
  style: "percent",
  maximumFractionDigits: 2
});

export function money(value: number) {
  return currency.format(value);
}

export function signedMoney(value: number) {
  const formatted = currency.format(Math.abs(value));
  if (value < 0) return `-${formatted}`;
  if (value > 0) return `+${formatted}`;
  return formatted;
}

export function compactMoney(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    notation: "compact",
    maximumFractionDigits: 1
  }).format(value);
}

export function decimal(value: number) {
  return number.format(value);
}

export function displayInput(value: number, format: "currency" | "number" | "percent") {
  if (!Number.isFinite(value)) return "";
  if (format === "percent") return String(Number((value * 100).toFixed(4)));
  if (format === "currency") return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value);
  return String(value);
}

export function parseInput(raw: string, format: "currency" | "number" | "percent") {
  const normalized = raw.replace(/[$,%\s]/g, "").replace(/,/g, "");
  const value = Number(normalized);
  if (!Number.isFinite(value)) return 0;
  return format === "percent" ? value / 100 : value;
}
