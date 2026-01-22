import { useState } from 'react';
import { Pencil, Trash2 } from 'lucide-react';
import { Income } from '../../types/income';
import { Table, Button, Modal } from '../common';
import { formatCurrency, formatDate } from '../../utils/formatters';

interface IncomeListProps {
  incomes: Income[];
  onEdit: (income: Income) => void;
  onDelete: (id: string) => void;
}

export function IncomeList({ incomes, onEdit, onDelete }: IncomeListProps) {
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [selectedIncome, setSelectedIncome] = useState<Income | null>(null);

  const handleDeleteClick = (income: Income) => {
    setSelectedIncome(income);
    setDeleteModalOpen(true);
  };

  const handleConfirmDelete = () => {
    if (selectedIncome) {
      onDelete(selectedIncome.id);
      setDeleteModalOpen(false);
      setSelectedIncome(null);
    }
  };

  const columns = [
    {
      key: 'date',
      header: 'Dátum',
      render: (income: Income) => formatDate(income.date),
    },
    {
      key: 'description',
      header: 'Leírás',
      render: (income: Income) => (
        <div>
          <p className="font-medium">{income.description}</p>
          <p className="text-xs text-gray-500">{income.customerName}</p>
        </div>
      ),
    },
    {
      key: 'amount',
      header: 'Összeg',
      render: (income: Income) => (
        <div className="text-right">
          {income.currency === 'EUR' && (
            <p className="font-semibold">{formatCurrency(income.amountOriginal, 'EUR')}</p>
          )}
          <p className={income.currency === 'EUR' ? 'text-sm text-gray-500' : 'font-semibold'}>
            {formatCurrency(income.amountHUF, 'HUF')}
          </p>
        </div>
      ),
      className: 'text-right',
    },
    {
      key: 'vatStatus',
      header: 'ÁFA',
      render: (income: Income) => {
        const labels: Record<string, string> = {
          non_eu_export: '0% Export',
          eu_reverse_charge: 'Ford. adó',
          domestic: 'Belföldi',
        };
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
            {labels[income.vatStatus]}
          </span>
        );
      },
    },
    {
      key: 'actions',
      header: '',
      render: (income: Income) => (
        <div className="flex items-center justify-end gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onEdit(income);
            }}
            className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
          >
            <Pencil className="w-4 h-4" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleDeleteClick(income);
            }}
            className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      ),
      className: 'w-24',
    },
  ];

  return (
    <>
      <Table
        data={incomes}
        columns={columns}
        keyExtractor={(income) => income.id}
        emptyMessage="Még nincs bevétel rögzítve"
      />

      <Modal
        isOpen={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        title="Bevétel törlése"
        size="sm"
      >
        <p className="text-gray-600 mb-6">
          Biztosan törölni szeretnéd ezt a bevételt?
          <br />
          <span className="font-medium">{selectedIncome?.description}</span>
        </p>
        <div className="flex justify-end gap-3">
          <Button variant="secondary" onClick={() => setDeleteModalOpen(false)}>
            Mégse
          </Button>
          <Button variant="danger" onClick={handleConfirmDelete}>
            Törlés
          </Button>
        </div>
      </Modal>
    </>
  );
}
