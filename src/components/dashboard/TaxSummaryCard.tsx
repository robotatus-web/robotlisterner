import { TaxCalculationResult } from '../../types/tax';
import { formatCurrency, formatPercent } from '../../utils/formatters';

interface TaxSummaryCardProps {
  calculation: TaxCalculationResult;
  totalIncomeEUR: number;
}

export function TaxSummaryCard({ calculation, totalIncomeEUR }: TaxSummaryCardProps) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4">
        <h3 className="text-lg font-semibold text-white">Adószámítás összesítő</h3>
        <p className="text-blue-100 text-sm">SZJA szerinti adózás</p>
      </div>

      <div className="p-6 space-y-6">
        {/* Bevétel és költség */}
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-gray-600">Bruttó bevétel</span>
            <div className="text-right">
              <span className="font-semibold">{formatCurrency(calculation.grossIncome, 'HUF')}</span>
              {totalIncomeEUR > 0 && (
                <p className="text-sm text-gray-500">{formatCurrency(totalIncomeEUR, 'EUR')}</p>
              )}
            </div>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-600">Levonható költségek</span>
            <span className="font-semibold text-red-600">
              -{formatCurrency(calculation.deductibleExpenses, 'HUF')}
            </span>
          </div>
          <div className="border-t pt-3 flex justify-between items-center">
            <span className="font-medium text-gray-900">Adóalap</span>
            <span className="font-bold text-lg">{formatCurrency(calculation.taxBase, 'HUF')}</span>
          </div>
        </div>

        {/* Adók */}
        <div className="bg-gray-50 rounded-lg p-4 space-y-3">
          <h4 className="font-medium text-gray-900">Fizetendő adók és járulékok</h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">SZJA (15%)</span>
              <span>{formatCurrency(calculation.incomeTax, 'HUF')}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">TB járulék (18,5%)</span>
              <span>{formatCurrency(calculation.healthInsurance, 'HUF')}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">SZOCHO (13%)</span>
              <span>{formatCurrency(calculation.socialTax, 'HUF')}</span>
            </div>
            <div className="border-t pt-2 flex justify-between font-medium">
              <span>Összes adó</span>
              <span className="text-red-600">{formatCurrency(calculation.totalTax, 'HUF')}</span>
            </div>
          </div>
        </div>

        {/* Nettó */}
        <div className="bg-green-50 rounded-lg p-4">
          <div className="flex justify-between items-center">
            <div>
              <p className="font-medium text-green-900">Nettó kivehető összeg</p>
              <p className="text-sm text-green-700">
                A bevétel {formatPercent(calculation.withdrawalRatio)}-a
              </p>
            </div>
            <span className="text-2xl font-bold text-green-700">
              {formatCurrency(calculation.netIncome, 'HUF')}
            </span>
          </div>
        </div>

        {/* Effektív adókulcs */}
        <div className="text-center pt-2">
          <p className="text-sm text-gray-500">
            Effektív adókulcs: <span className="font-semibold">{formatPercent(calculation.effectiveTaxRate)}</span>
          </p>
          <p className="text-sm text-gray-500">
            Negyedéves adóelőleg: <span className="font-semibold">{formatCurrency(calculation.quarterlyAdvance, 'HUF')}</span>
          </p>
        </div>
      </div>
    </div>
  );
}
