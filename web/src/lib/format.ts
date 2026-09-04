export function formatWeight(kg: number): string {
  return kg >= 1000 ? `${(kg / 1000).toFixed(2)} t` : `${kg.toFixed(0)} kg`;
}

export function formatCurrency(n: number): string {
  return `$${n.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

export function formatNumber(n: number): string {
  return n.toLocaleString();
}

export function formatPercent(fraction: number): string {
  return `${Math.round(fraction * 100)}%`;
}
