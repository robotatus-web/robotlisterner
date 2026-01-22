export function formatCurrency(amount: number, currency: 'HUF' | 'EUR' = 'HUF'): string {
  return new Intl.NumberFormat('hu-HU', {
    style: 'currency',
    currency,
    minimumFractionDigits: currency === 'HUF' ? 0 : 2,
    maximumFractionDigits: currency === 'HUF' ? 0 : 2,
  }).format(amount);
}

export function formatNumber(num: number, decimals: number = 0): string {
  return new Intl.NumberFormat('hu-HU', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(num);
}

export function formatDate(dateString: string): string {
  return new Intl.DateTimeFormat('hu-HU', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(new Date(dateString));
}

export function formatPercent(value: number): string {
  return new Intl.NumberFormat('hu-HU', {
    style: 'percent',
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(value / 100);
}

export function formatExchangeRate(rate: number): string {
  return new Intl.NumberFormat('hu-HU', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(rate);
}

export function generateId(): string {
  return crypto.randomUUID();
}

export function getCurrentISODate(): string {
  return new Date().toISOString().split('T')[0];
}
