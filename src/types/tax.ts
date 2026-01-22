// Magyar adószámítási típusok - SZJA szerinti adózás

export interface TaxRates {
  szja: number;              // Személyi jövedelemadó: 15%
  socialTax: number;         // SZOCHO: 13%
  healthInsurance: number;   // TB járulék: 18.5%
}

export interface TaxCalculationInput {
  year: number;
  totalIncomeHUF: number;      // Összes bevétel HUF-ban
  totalExpensesHUF: number;    // Összes levonható költség HUF-ban
  minimumWage: number;         // Minimálbér (havi)
  monthsActive: number;        // Aktív hónapok száma
}

export interface TaxCalculationResult {
  // Alap számok
  grossIncome: number;           // Bruttó bevétel
  deductibleExpenses: number;    // Levonható költségek
  taxBase: number;               // Adóalap (bevétel - költségek)

  // Járulékalap (minimum a minimálbér)
  contributionBase: number;      // Járulékalap
  minimumContributionBase: number; // Minimum járulékalap (minimálbér * hónapok)

  // Adók és járulékok
  incomeTax: number;             // SZJA (15%)
  socialTax: number;             // SZOCHO (13%)
  healthInsurance: number;       // TB járulék (18.5%)

  // Összesítés
  totalTax: number;              // Összes adó és járulék
  netIncome: number;             // Nettó jövedelem (kivehető)

  // Arányok
  effectiveTaxRate: number;      // Effektív adókulcs (%)
  withdrawalRatio: number;       // Kivehető arány (%)

  // Negyedéves bontás
  quarterlyAdvance: number;      // Negyedéves adóelőleg
}

export interface MonthlyBreakdown {
  month: number;
  income: number;
  expenses: number;
  taxBase: number;
  estimatedTax: number;
}

// 2024-es adókulcsok és minimálbér
export const TAX_RATES_2024: TaxRates = {
  szja: 0.15,
  socialTax: 0.13,
  healthInsurance: 0.185,
};

export const MINIMUM_WAGE_2024 = 266800; // Ft/hó (2024)
export const MINIMUM_WAGE_2025 = 290800; // Ft/hó (2025)
