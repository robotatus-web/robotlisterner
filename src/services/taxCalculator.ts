import {
  TaxCalculationInput,
  TaxCalculationResult,
  TaxRates,
  TAX_RATES_2024,
  MINIMUM_WAGE_2024,
  MINIMUM_WAGE_2025,
} from '../types/tax';

// Adókulcsok év szerint
function getTaxRates(year: number): TaxRates {
  // 2024-től változatlan kulcsok
  return TAX_RATES_2024;
}

// Minimálbér év szerint
export function getMinimumWage(year: number): number {
  if (year >= 2025) return MINIMUM_WAGE_2025;
  return MINIMUM_WAGE_2024;
}

/**
 * Magyar egyéni vállalkozó adószámítás - SZJA szerinti adózás
 * (tételes költségelszámolással)
 */
export function calculateTax(input: TaxCalculationInput): TaxCalculationResult {
  const rates = getTaxRates(input.year);

  // Alapszámok
  const grossIncome = input.totalIncomeHUF;
  const deductibleExpenses = input.totalExpensesHUF;

  // Adóalap = Bevétel - Elismert költségek
  const taxBase = Math.max(0, grossIncome - deductibleExpenses);

  // Minimum járulékalap (minimálbér * aktív hónapok)
  const minimumContributionBase = input.minimumWage * input.monthsActive;

  // Járulékalap: a tényleges jövedelem vagy a minimum, amelyik nagyobb
  const contributionBase = Math.max(taxBase, minimumContributionBase);

  // SZJA - az adóalapból számítva
  const incomeTax = Math.round(taxBase * rates.szja);

  // SZOCHO - a járulékalapból
  const socialTax = Math.round(contributionBase * rates.socialTax);

  // TB járulék - a járulékalapból
  const healthInsurance = Math.round(contributionBase * rates.healthInsurance);

  // Összes adó és járulék
  const totalTax = incomeTax + socialTax + healthInsurance;

  // Nettó jövedelem (amit ki lehet venni)
  const netIncome = grossIncome - deductibleExpenses - totalTax;

  // Effektív adókulcs
  const effectiveTaxRate = grossIncome > 0
    ? (totalTax / grossIncome) * 100
    : 0;

  // Kivehető arány
  const withdrawalRatio = grossIncome > 0
    ? (netIncome / grossIncome) * 100
    : 0;

  // Negyedéves adóelőleg (éves adó / 4)
  const quarterlyAdvance = Math.round(totalTax / 4);

  return {
    grossIncome,
    deductibleExpenses,
    taxBase,
    contributionBase,
    minimumContributionBase,
    incomeTax,
    socialTax,
    healthInsurance,
    totalTax,
    netIncome,
    effectiveTaxRate,
    withdrawalRatio,
    quarterlyAdvance,
  };
}

/**
 * Havi bontás készítése
 */
export function calculateMonthlyBreakdown(
  incomes: { date: string; amountHUF: number }[],
  expenses: { date: string; amount: number; isDeductible: boolean }[],
  year: number
): { month: number; income: number; expenses: number; cumulative: TaxCalculationResult }[] {
  const result: { month: number; income: number; expenses: number; cumulative: TaxCalculationResult }[] = [];
  const minimumWage = getMinimumWage(year);

  let cumulativeIncome = 0;
  let cumulativeExpenses = 0;

  for (let month = 1; month <= 12; month++) {
    // Adott havi bevételek
    const monthlyIncome = incomes
      .filter(i => {
        const d = new Date(i.date);
        return d.getFullYear() === year && d.getMonth() + 1 === month;
      })
      .reduce((sum, i) => sum + i.amountHUF, 0);

    // Adott havi levonható költségek
    const monthlyExpenses = expenses
      .filter(e => {
        const d = new Date(e.date);
        return d.getFullYear() === year && d.getMonth() + 1 === month && e.isDeductible;
      })
      .reduce((sum, e) => sum + e.amount, 0);

    cumulativeIncome += monthlyIncome;
    cumulativeExpenses += monthlyExpenses;

    // Kumulatív adószámítás
    const cumulative = calculateTax({
      year,
      totalIncomeHUF: cumulativeIncome,
      totalExpensesHUF: cumulativeExpenses,
      minimumWage,
      monthsActive: month,
    });

    result.push({
      month,
      income: monthlyIncome,
      expenses: monthlyExpenses,
      cumulative,
    });
  }

  return result;
}

/**
 * Negyedéves adóelőleg számítás
 */
export function calculateQuarterlyAdvance(
  currentQuarter: number,
  yearToDateIncome: number,
  yearToDateExpenses: number,
  year: number
): { quarterlyTax: number; paidSoFar: number; dueNow: number } {
  const minimumWage = getMinimumWage(year);
  const monthsActive = currentQuarter * 3;

  const result = calculateTax({
    year,
    totalIncomeHUF: yearToDateIncome,
    totalExpensesHUF: yearToDateExpenses,
    minimumWage,
    monthsActive,
  });

  // Az aktuális negyedévig esedékes adó
  const quarterlyTax = Math.round(result.totalTax * (currentQuarter / 4));

  // Eddig fizetett (előző negyedévek)
  const paidSoFar = Math.round(result.totalTax * ((currentQuarter - 1) / 4));

  // Most esedékes
  const dueNow = quarterlyTax - paidSoFar;

  return { quarterlyTax, paidSoFar, dueNow };
}
