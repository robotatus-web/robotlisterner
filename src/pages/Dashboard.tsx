import { useEffect, useMemo } from 'react';
import { TrendingUp, TrendingDown, Calculator, Wallet } from 'lucide-react';
import { Header } from '../components/layout';
import { Card, StatCard } from '../components/common';
import { TaxSummaryCard, RevenueChart, WithdrawalGauge } from '../components/dashboard';
import { useIncomeStore, useExpenseStore, useSettingsStore } from '../store';
import { calculateTax, getMinimumWage } from '../services/taxCalculator';
import { formatCurrency } from '../utils/formatters';

export function Dashboard() {
  const { incomes, loadIncomes, getIncomesByYear, getTotalIncomeHUF, getTotalIncomeEUR } = useIncomeStore();
  const { expenses, loadExpenses, getExpensesByYear, getDeductibleExpenses } = useExpenseStore();
  const { selectedYear, loadSettings } = useSettingsStore();

  useEffect(() => {
    loadIncomes();
    loadExpenses();
    loadSettings();
  }, [loadIncomes, loadExpenses, loadSettings]);

  const yearIncomes = getIncomesByYear(selectedYear);
  const yearExpenses = getExpensesByYear(selectedYear);
  const totalIncomeHUF = getTotalIncomeHUF(selectedYear);
  const totalIncomeEUR = getTotalIncomeEUR(selectedYear);
  const deductibleExpenses = getDeductibleExpenses(selectedYear);

  const taxCalculation = useMemo(() => {
    return calculateTax({
      year: selectedYear,
      totalIncomeHUF,
      totalExpensesHUF: deductibleExpenses,
      minimumWage: getMinimumWage(selectedYear),
      monthsActive: 12,
    });
  }, [selectedYear, totalIncomeHUF, deductibleExpenses]);

  // Havi bontás a grafikonhoz
  const monthlyData = useMemo(() => {
    const data = Array.from({ length: 12 }, (_, i) => ({
      month: String(i + 1),
      income: 0,
      expense: 0,
    }));

    yearIncomes.forEach((income) => {
      const month = new Date(income.date).getMonth();
      data[month].income += income.amountHUF;
    });

    yearExpenses.forEach((expense) => {
      const month = new Date(expense.date).getMonth();
      data[month].expense += expense.amount;
    });

    return data;
  }, [yearIncomes, yearExpenses]);

  return (
    <div>
      <Header
        title="Dashboard"
        subtitle={`Pénzügyi összesítő - ${selectedYear}`}
      />

      <div className="p-8">
        {/* Stat cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            title="Összes bevétel"
            value={formatCurrency(totalIncomeHUF, 'HUF')}
            subtitle={totalIncomeEUR > 0 ? formatCurrency(totalIncomeEUR, 'EUR') : undefined}
            icon={<TrendingUp className="w-6 h-6" />}
          />
          <StatCard
            title="Összes kiadás"
            value={formatCurrency(yearExpenses.reduce((sum, e) => sum + e.amount, 0), 'HUF')}
            subtitle={`Levonható: ${formatCurrency(deductibleExpenses, 'HUF')}`}
            icon={<TrendingDown className="w-6 h-6" />}
          />
          <StatCard
            title="Fizetendő adók"
            value={formatCurrency(taxCalculation.totalTax, 'HUF')}
            subtitle="SZJA + TB + SZOCHO"
            icon={<Calculator className="w-6 h-6" />}
          />
          <StatCard
            title="Nettó kivehető"
            value={formatCurrency(taxCalculation.netIncome, 'HUF')}
            subtitle={`A bevétel ${taxCalculation.withdrawalRatio.toFixed(0)}%-a`}
            icon={<Wallet className="w-6 h-6" />}
          />
        </div>

        {/* Main content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Chart */}
          <div className="lg:col-span-2">
            <Card title="Bevételek és kiadások" subtitle="Havi bontás">
              <RevenueChart data={monthlyData} />
            </Card>
          </div>

          {/* Withdrawal gauge */}
          <div>
            <Card title="Kivehető arány">
              <div className="flex justify-center py-4">
                <WithdrawalGauge
                  percentage={taxCalculation.withdrawalRatio}
                  netAmount={taxCalculation.netIncome}
                  grossAmount={totalIncomeHUF}
                />
              </div>
            </Card>
          </div>
        </div>

        {/* Tax summary */}
        <div className="mt-8">
          <TaxSummaryCard
            calculation={taxCalculation}
            totalIncomeEUR={totalIncomeEUR}
          />
        </div>

        {/* Quick stats */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card title="Tranzakciók">
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Bevételek száma</span>
                <span className="font-semibold">{yearIncomes.length} db</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Kiadások száma</span>
                <span className="font-semibold">{yearExpenses.length} db</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Átlag bevétel</span>
                <span className="font-semibold">
                  {yearIncomes.length > 0
                    ? formatCurrency(totalIncomeHUF / yearIncomes.length, 'HUF')
                    : '-'}
                </span>
              </div>
            </div>
          </Card>

          <Card title="Adóelőleg">
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Negyedéves előleg</span>
                <span className="font-semibold">{formatCurrency(taxCalculation.quarterlyAdvance, 'HUF')}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Éves becsült adó</span>
                <span className="font-semibold">{formatCurrency(taxCalculation.totalTax, 'HUF')}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Effektív adókulcs</span>
                <span className="font-semibold">{taxCalculation.effectiveTaxRate.toFixed(1)}%</span>
              </div>
            </div>
          </Card>

          <Card title="Járulékok">
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">SZJA (15%)</span>
                <span className="font-semibold">{formatCurrency(taxCalculation.incomeTax, 'HUF')}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">TB (18,5%)</span>
                <span className="font-semibold">{formatCurrency(taxCalculation.healthInsurance, 'HUF')}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">SZOCHO (13%)</span>
                <span className="font-semibold">{formatCurrency(taxCalculation.socialTax, 'HUF')}</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
