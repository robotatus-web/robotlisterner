import { useState, useEffect } from 'react';
import { Button, Input, Select } from '../common';
import { IncomeCategory, VatStatus, Currency } from '../../types/income';
import { getExchangeRate, convertEURtoHUF } from '../../services/exchangeRate';
import { formatCurrency, formatExchangeRate, getCurrentISODate } from '../../utils/formatters';

const categoryOptions: { value: IncomeCategory; label: string }[] = [
  { value: 'service', label: 'Szolgáltatás' },
  { value: 'consulting', label: 'Konzultáció' },
  { value: 'product', label: 'Termék' },
  { value: 'royalty', label: 'Jogdíj' },
  { value: 'other', label: 'Egyéb' },
];

const currencyOptions: { value: Currency; label: string }[] = [
  { value: 'EUR', label: 'EUR' },
  { value: 'HUF', label: 'HUF' },
];

const vatStatusOptions: { value: VatStatus; label: string }[] = [
  { value: 'non_eu_export', label: 'EU-n kívüli export (0% ÁFA)' },
  { value: 'eu_reverse_charge', label: 'EU fordított adózás' },
  { value: 'domestic', label: 'Belföldi' },
];

interface IncomeFormProps {
  onSubmit: (data: {
    date: string;
    description: string;
    category: IncomeCategory;
    currency: Currency;
    amountOriginal: number;
    exchangeRate: number;
    customerName: string;
    customerCountry: string;
    invoiceNumber?: string;
    vatStatus: VatStatus;
    notes?: string;
  }) => void;
  onCancel: () => void;
  initialData?: Partial<{
    date: string;
    description: string;
    category: IncomeCategory;
    currency: Currency;
    amountOriginal: number;
    exchangeRate: number;
    customerName: string;
    customerCountry: string;
    invoiceNumber: string;
    vatStatus: VatStatus;
    notes: string;
  }>;
}

export function IncomeForm({ onSubmit, onCancel, initialData }: IncomeFormProps) {
  const [date, setDate] = useState(initialData?.date || getCurrentISODate());
  const [description, setDescription] = useState(initialData?.description || '');
  const [category, setCategory] = useState<IncomeCategory>(initialData?.category || 'service');
  const [currency, setCurrency] = useState<Currency>(initialData?.currency || 'EUR');
  const [amountOriginal, setAmountOriginal] = useState(initialData?.amountOriginal?.toString() || '');
  const [exchangeRate, setExchangeRate] = useState(initialData?.exchangeRate?.toString() || '');
  const [customerName, setCustomerName] = useState(initialData?.customerName || '');
  const [customerCountry, setCustomerCountry] = useState(initialData?.customerCountry || '');
  const [invoiceNumber, setInvoiceNumber] = useState(initialData?.invoiceNumber || '');
  const [vatStatus, setVatStatus] = useState<VatStatus>(initialData?.vatStatus || 'non_eu_export');
  const [notes, setNotes] = useState(initialData?.notes || '');
  const [isLoadingRate, setIsLoadingRate] = useState(false);

  // Árfolyam lekérés dátum változáskor
  useEffect(() => {
    if (currency === 'EUR' && date) {
      setIsLoadingRate(true);
      getExchangeRate(date).then((rate) => {
        setExchangeRate(rate.toFixed(2));
        setIsLoadingRate(false);
      });
    }
  }, [date, currency]);

  const handleFetchRate = async () => {
    setIsLoadingRate(true);
    const rate = await getExchangeRate(date);
    setExchangeRate(rate.toFixed(2));
    setIsLoadingRate(false);
  };

  const calculatedHUF = currency === 'EUR' && amountOriginal && exchangeRate
    ? convertEURtoHUF(parseFloat(amountOriginal), parseFloat(exchangeRate))
    : parseFloat(amountOriginal) || 0;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      date,
      description,
      category,
      currency,
      amountOriginal: parseFloat(amountOriginal),
      exchangeRate: currency === 'EUR' ? parseFloat(exchangeRate) : 1,
      customerName,
      customerCountry,
      invoiceNumber: invoiceNumber || undefined,
      vatStatus,
      notes: notes || undefined,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <Input
          label="Teljesítés dátuma"
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          required
        />
        <Select
          label="Kategória"
          options={categoryOptions}
          value={category}
          onChange={(e) => setCategory(e.target.value as IncomeCategory)}
        />
      </div>

      <Input
        label="Leírás"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        placeholder="Pl. Webfejlesztési szolgáltatás"
        required
      />

      <div className="grid grid-cols-3 gap-4">
        <Select
          label="Pénznem"
          options={currencyOptions}
          value={currency}
          onChange={(e) => setCurrency(e.target.value as Currency)}
        />
        <Input
          label={`Összeg (${currency})`}
          type="number"
          step="0.01"
          min="0"
          value={amountOriginal}
          onChange={(e) => setAmountOriginal(e.target.value)}
          placeholder="0.00"
          required
        />
        {currency === 'EUR' && (
          <div>
            <Input
              label="MNB árfolyam"
              type="number"
              step="0.01"
              value={exchangeRate}
              onChange={(e) => setExchangeRate(e.target.value)}
              rightElement={
                <button
                  type="button"
                  onClick={handleFetchRate}
                  disabled={isLoadingRate}
                  className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                >
                  {isLoadingRate ? '...' : 'Lekérés'}
                </button>
              }
              required
            />
          </div>
        )}
      </div>

      {currency === 'EUR' && amountOriginal && exchangeRate && (
        <div className="bg-blue-50 rounded-lg p-4">
          <p className="text-sm text-gray-600">
            HUF összeg: <span className="font-semibold text-gray-900">{formatCurrency(calculatedHUF, 'HUF')}</span>
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Árfolyam: {formatExchangeRate(parseFloat(exchangeRate))} Ft/EUR
          </p>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <Input
          label="Ügyfél neve"
          value={customerName}
          onChange={(e) => setCustomerName(e.target.value)}
          placeholder="Pl. Acme Corp"
          required
        />
        <Input
          label="Ügyfél országa"
          value={customerCountry}
          onChange={(e) => setCustomerCountry(e.target.value)}
          placeholder="Pl. USA"
          required
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Input
          label="Számla száma"
          value={invoiceNumber}
          onChange={(e) => setInvoiceNumber(e.target.value)}
          placeholder="Pl. INV-2024-001"
        />
        <Select
          label="ÁFA státusz"
          options={vatStatusOptions}
          value={vatStatus}
          onChange={(e) => setVatStatus(e.target.value as VatStatus)}
        />
      </div>

      <Input
        label="Megjegyzés"
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        placeholder="Opcionális megjegyzés..."
      />

      <div className="flex justify-end gap-3 pt-4">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Mégse
        </Button>
        <Button type="submit">
          Mentés
        </Button>
      </div>
    </form>
  );
}
