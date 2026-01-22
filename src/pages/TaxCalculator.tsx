import { useEffect, useMemo, useState } from 'react';
import { Header } from '../components/layout';
import { Card, Input } from '../components/common';
import { TaxSummaryCard } from '../components/dashboard';
import { useIncomeStore, useExpenseStore, useSettingsStore } from '../store';
import { calculateTax, getMinimumWage, calculateQuarterlyAdvance } from '../services/taxCalculator';
import { formatCurrency } from '../utils/formatters';

export function TaxCalculator() {
  const { loadIncomes, getTotalIncomeHUF, getTotalIncomeEUR } = useIncomeStore();
  const { loadExpenses, getDeductibleExpenses } = useExpenseStore();
  const { selectedYear, loadSettings } = useSettingsStore();

  const [monthsActive, setMonthsActive] = useState(12);
  const [simulatedIncome, setSimulatedIncome] = useState('');
  const [simulatedExpenses, setSimulatedExpenses] = useState('');

  useEffect(() => {
    loadIncomes();
    loadExpenses();
    loadSettings();
  }, [loadIncomes, loadExpenses, loadSettings]);

  const actualIncomeHUF = getTotalIncomeHUF(selectedYear);
  const actualIncomeEUR = getTotalIncomeEUR(selectedYear);
  const actualExpenses = getDeductibleExpenses(selectedYear);
  const minimumWage = getMinimumWage(selectedYear);

  // Aktuális számítás
  const actualCalculation = useMemo(() => {
    return calculateTax({
      year: selectedYear,
      totalIncomeHUF: actualIncomeHUF,
      totalExpensesHUF: actualExpenses,
      minimumWage,
      monthsActive,
    });
  }, [selectedYear, actualIncomeHUF, actualExpenses, minimumWage, monthsActive]);

  // Szimulált számítás
  const simulatedCalculation = useMemo(() => {
    const income = simulatedIncome ? parseFloat(simulatedIncome) : actualIncomeHUF;
    const expenses = simulatedExpenses ? parseFloat(simulatedExpenses) : actualExpenses;

    return calculateTax({
      year: selectedYear,
      totalIncomeHUF: income,
      totalExpensesHUF: expenses,
      minimumWage,
      monthsActive,
    });
  }, [selectedYear, simulatedIncome, simulatedExpenses, actualIncomeHUF, actualExpenses, minimumWage, monthsActive]);

  // Negyedéves adóelőleg
  const currentQuarter = Math.ceil((new Date().getMonth() + 1) / 3);
  const quarterlyAdvance = calculateQuarterlyAdvance(
    currentQuarter,
    actualIncomeHUF,
    actualExpenses,
    selectedYear
  );

  const isSimulating = simulatedIncome || simulatedExpenses;

  return (
    <div>
      <Header
        title="Adókalkulátor"
        subtitle="SZJA szerinti adózás - tételes költségelszámolás"
      />

      <div className="p-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Aktuális adatok */}
          <div>
            <Card title="Aktuális adatok" subtitle={`${selectedYear}. év alapján`}>
              <div className="space-y-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-500">Bevétel (HUF)</p>
                      <p className="text-lg font-semibold">{formatCurrency(actualIncomeHUF, 'HUF')}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Bevétel (EUR)</p>
                      <p className="text-lg font-semibold">{formatCurrency(actualIncomeEUR, 'EUR')}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Levonható költség</p>
                      <p className="text-lg font-semibold">{formatCurrency(actualExpenses, 'HUF')}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Minimálbér ({selectedYear})</p>
                      <p className="text-lg font-semibold">{formatCurrency(minimumWage, 'HUF')}/hó</p>
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Aktív hónapok száma
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="12"
                    value={monthsActive}
                    onChange={(e) => setMonthsActive(parseInt(e.target.value))}
                    className="w-full"
                  />
                  <div className="flex justify-between text-sm text-gray-500 mt-1">
                    <span>1 hónap</span>
                    <span className="font-semibold">{monthsActive} hónap</span>
                    <span>12 hónap</span>
                  </div>
                </div>
              </div>
            </Card>

            {/* Negyedéves előleg */}
            <Card title="Negyedéves adóelőleg" className="mt-6">
              <div className="space-y-4">
                <div className="flex justify-between items-center p-4 bg-blue-50 rounded-lg">
                  <div>
                    <p className="font-medium text-blue-900">Aktuális negyedév: Q{currentQuarter}</p>
                    <p className="text-sm text-blue-700">Esedékes adóelőleg</p>
                  </div>
                  <span className="text-2xl font-bold text-blue-700">
                    {formatCurrency(quarterlyAdvance.dueNow, 'HUF')}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-gray-500">Eddig esedékes (Q1-Q{currentQuarter})</p>
                    <p className="font-semibold">{formatCurrency(quarterlyAdvance.quarterlyTax, 'HUF')}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Előző negyedévek (Q1-Q{currentQuarter - 1})</p>
                    <p className="font-semibold">{formatCurrency(quarterlyAdvance.paidSoFar, 'HUF')}</p>
                  </div>
                </div>

                <div className="text-xs text-gray-500 p-3 bg-gray-50 rounded-lg">
                  <p className="font-medium mb-1">Adóelőleg határidők:</p>
                  <ul className="space-y-1">
                    <li>Q1 (jan-már): április 12.</li>
                    <li>Q2 (ápr-jún): július 12.</li>
                    <li>Q3 (júl-szep): október 12.</li>
                    <li>Q4 (okt-dec): január 12. (következő év)</li>
                  </ul>
                </div>
              </div>
            </Card>
          </div>

          {/* Szimuláció */}
          <div>
            <Card title="Mi lenne ha...?" subtitle="Szimuláció más értékekkel">
              <div className="space-y-4 mb-6">
                <Input
                  label="Szimulált bevétel (HUF)"
                  type="number"
                  value={simulatedIncome}
                  onChange={(e) => setSimulatedIncome(e.target.value)}
                  placeholder={actualIncomeHUF.toString()}
                  helperText="Hagyd üresen az aktuális érték használatához"
                />
                <Input
                  label="Szimulált költségek (HUF)"
                  type="number"
                  value={simulatedExpenses}
                  onChange={(e) => setSimulatedExpenses(e.target.value)}
                  placeholder={actualExpenses.toString()}
                  helperText="Hagyd üresen az aktuális érték használatához"
                />
              </div>

              {isSimulating && (
                <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg mb-4">
                  <p className="text-sm text-yellow-800">
                    Szimulált értékek alapján számolva
                  </p>
                </div>
              )}
            </Card>

            {/* Eredmény */}
            <div className="mt-6">
              <TaxSummaryCard
                calculation={isSimulating ? simulatedCalculation : actualCalculation}
                totalIncomeEUR={isSimulating ? 0 : actualIncomeEUR}
              />
            </div>
          </div>
        </div>

        {/* Adókulcsok info */}
        <Card title="Aktuális adókulcsok" className="mt-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-4 bg-gray-50 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-2">SZJA</h4>
              <p className="text-3xl font-bold text-blue-600">15%</p>
              <p className="text-sm text-gray-500 mt-1">Személyi jövedelemadó</p>
              <p className="text-xs text-gray-400 mt-2">Az adóalapból (bevétel - költség)</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-2">TB járulék</h4>
              <p className="text-3xl font-bold text-green-600">18,5%</p>
              <p className="text-sm text-gray-500 mt-1">Társadalombiztosítási járulék</p>
              <p className="text-xs text-gray-400 mt-2">Minimum a minimálbér után</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-2">SZOCHO</h4>
              <p className="text-3xl font-bold text-purple-600">13%</p>
              <p className="text-sm text-gray-500 mt-1">Szociális hozzájárulási adó</p>
              <p className="text-xs text-gray-400 mt-2">Minimum a minimálbér után</p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
