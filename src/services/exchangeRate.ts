// MNB árfolyam szolgáltatás
// Az MNB hivatalos árfolyamait használjuk

interface ExchangeRateCache {
  [date: string]: number;
}

const cache: ExchangeRateCache = {};

// MNB árfolyam API (CORS proxy-val vagy backend-del működne élesben)
// Fejlesztési célra mock adatokat használunk
const MOCK_RATES: ExchangeRateCache = {
  // 2024-es átlagos árfolyamok
  '2024-01': 382.50,
  '2024-02': 385.20,
  '2024-03': 394.80,
  '2024-04': 393.10,
  '2024-05': 389.40,
  '2024-06': 395.60,
  '2024-07': 392.30,
  '2024-08': 396.50,
  '2024-09': 398.20,
  '2024-10': 400.15,
  '2024-11': 405.80,
  '2024-12': 410.25,
  // 2025-ös árfolyamok
  '2025-01': 408.50,
  '2025-02': 405.30,
  '2025-03': 402.80,
  '2025-04': 399.60,
  '2025-05': 397.20,
  '2025-06': 395.40,
  '2025-07': 398.10,
  '2025-08': 401.50,
  '2025-09': 403.80,
  '2025-10': 406.20,
  '2025-11': 408.90,
  '2025-12': 410.50,
  // 2026
  '2026-01': 412.30,
};

// Alapértelmezett árfolyam ha nincs adat
const DEFAULT_RATE = 400.00;

export async function getExchangeRate(date: string): Promise<number> {
  // Ellenőrizzük a cache-t
  if (cache[date]) {
    return cache[date];
  }

  // Hónap alapján keresünk mock adatot
  const monthKey = date.substring(0, 7);

  if (MOCK_RATES[monthKey]) {
    // Kis random variáció a napok között
    const dayOfMonth = parseInt(date.substring(8, 10));
    const variation = (dayOfMonth - 15) * 0.1;
    const rate = MOCK_RATES[monthKey] + variation;
    cache[date] = rate;
    return rate;
  }

  // Ha nincs adat, használjuk az alapértelmezettet
  cache[date] = DEFAULT_RATE;
  return DEFAULT_RATE;
}

export async function getCurrentExchangeRate(): Promise<number> {
  const today = new Date().toISOString().split('T')[0];
  return getExchangeRate(today);
}

export function convertEURtoHUF(amountEUR: number, exchangeRate: number): number {
  return Math.round(amountEUR * exchangeRate);
}

export function convertHUFtoEUR(amountHUF: number, exchangeRate: number): number {
  return amountHUF / exchangeRate;
}

// Valós MNB API hívás (éles környezetben backend proxy-n keresztül)
export async function fetchMNBExchangeRate(date: string): Promise<number | null> {
  try {
    // Ez egy példa URL - éles környezetben saját backend kellene
    // az MNB SOAP API-hoz vagy a Magyar Nemzeti Bank JSON feed-jéhez
    const response = await fetch(
      `https://api.exchangerate.host/convert?from=EUR&to=HUF&date=${date}`
    );

    if (!response.ok) {
      throw new Error('Failed to fetch exchange rate');
    }

    const data = await response.json();
    return data.result || null;
  } catch (error) {
    console.warn('Could not fetch live exchange rate, using mock data');
    return null;
  }
}
