import { useState } from 'react';
import { Button, Input, Select } from '../common';
import { ExpenseCategory, EXPENSE_CATEGORY_LABELS } from '../../types/expense';
import { getCurrentISODate } from '../../utils/formatters';

const categoryOptions = Object.entries(EXPENSE_CATEGORY_LABELS).map(([value, label]) => ({
  value,
  label,
}));

interface ExpenseFormProps {
  onSubmit: (data: {
    date: string;
    description: string;
    category: ExpenseCategory;
    amount: number;
    vatAmount: number;
    netAmount: number;
    isDeductible: boolean;
    receiptNumber?: string;
    vendor?: string;
    notes?: string;
  }) => void;
  onCancel: () => void;
  initialData?: Partial<{
    date: string;
    description: string;
    category: ExpenseCategory;
    amount: number;
    vatAmount: number;
    netAmount: number;
    isDeductible: boolean;
    receiptNumber: string;
    vendor: string;
    notes: string;
  }>;
}

export function ExpenseForm({ onSubmit, onCancel, initialData }: ExpenseFormProps) {
  const [date, setDate] = useState(initialData?.date || getCurrentISODate());
  const [description, setDescription] = useState(initialData?.description || '');
  const [category, setCategory] = useState<ExpenseCategory>(initialData?.category || 'other');
  const [grossAmount, setGrossAmount] = useState(initialData?.amount?.toString() || '');
  const [vatRate, setVatRate] = useState('27');
  const [isDeductible, setIsDeductible] = useState(initialData?.isDeductible ?? true);
  const [receiptNumber, setReceiptNumber] = useState(initialData?.receiptNumber || '');
  const [vendor, setVendor] = useState(initialData?.vendor || '');
  const [notes, setNotes] = useState(initialData?.notes || '');

  const gross = parseFloat(grossAmount) || 0;
  const vatMultiplier = 1 + parseFloat(vatRate) / 100;
  const netAmount = Math.round(gross / vatMultiplier);
  const vatAmount = gross - netAmount;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      date,
      description,
      category,
      amount: gross,
      vatAmount,
      netAmount,
      isDeductible,
      receiptNumber: receiptNumber || undefined,
      vendor: vendor || undefined,
      notes: notes || undefined,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <Input
          label="Dátum"
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          required
        />
        <Select
          label="Kategória"
          options={categoryOptions}
          value={category}
          onChange={(e) => setCategory(e.target.value as ExpenseCategory)}
        />
      </div>

      <Input
        label="Leírás"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        placeholder="Pl. Laptop vásárlás"
        required
      />

      <div className="grid grid-cols-2 gap-4">
        <Input
          label="Bruttó összeg (HUF)"
          type="number"
          min="0"
          value={grossAmount}
          onChange={(e) => setGrossAmount(e.target.value)}
          placeholder="0"
          required
        />
        <Select
          label="ÁFA kulcs"
          options={[
            { value: '0', label: '0%' },
            { value: '5', label: '5%' },
            { value: '18', label: '18%' },
            { value: '27', label: '27%' },
          ]}
          value={vatRate}
          onChange={(e) => setVatRate(e.target.value)}
        />
      </div>

      {grossAmount && (
        <div className="bg-gray-50 rounded-lg p-4 grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-500">Nettó összeg</p>
            <p className="font-semibold">{netAmount.toLocaleString('hu-HU')} Ft</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">ÁFA összeg</p>
            <p className="font-semibold">{vatAmount.toLocaleString('hu-HU')} Ft</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <Input
          label="Szállító"
          value={vendor}
          onChange={(e) => setVendor(e.target.value)}
          placeholder="Pl. Media Markt"
        />
        <Input
          label="Bizonylat száma"
          value={receiptNumber}
          onChange={(e) => setReceiptNumber(e.target.value)}
          placeholder="Pl. SZ-2024-001"
        />
      </div>

      <div className="flex items-center gap-3">
        <input
          type="checkbox"
          id="isDeductible"
          checked={isDeductible}
          onChange={(e) => setIsDeductible(e.target.checked)}
          className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
        />
        <label htmlFor="isDeductible" className="text-sm text-gray-700">
          Adóból levonható költség
        </label>
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
