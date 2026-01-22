import { useState } from 'react';
import { Pencil, Trash2, Check, X } from 'lucide-react';
import { Expense, EXPENSE_CATEGORY_LABELS } from '../../types/expense';
import { Table, Button, Modal } from '../common';
import { formatCurrency, formatDate } from '../../utils/formatters';

interface ExpenseListProps {
  expenses: Expense[];
  onEdit: (expense: Expense) => void;
  onDelete: (id: string) => void;
}

export function ExpenseList({ expenses, onEdit, onDelete }: ExpenseListProps) {
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [selectedExpense, setSelectedExpense] = useState<Expense | null>(null);

  const handleDeleteClick = (expense: Expense) => {
    setSelectedExpense(expense);
    setDeleteModalOpen(true);
  };

  const handleConfirmDelete = () => {
    if (selectedExpense) {
      onDelete(selectedExpense.id);
      setDeleteModalOpen(false);
      setSelectedExpense(null);
    }
  };

  const columns = [
    {
      key: 'date',
      header: 'Dátum',
      render: (expense: Expense) => formatDate(expense.date),
    },
    {
      key: 'description',
      header: 'Leírás',
      render: (expense: Expense) => (
        <div>
          <p className="font-medium">{expense.description}</p>
          <p className="text-xs text-gray-500">{expense.vendor}</p>
        </div>
      ),
    },
    {
      key: 'category',
      header: 'Kategória',
      render: (expense: Expense) => (
        <span className="text-sm text-gray-600">
          {EXPENSE_CATEGORY_LABELS[expense.category]}
        </span>
      ),
    },
    {
      key: 'amount',
      header: 'Összeg',
      render: (expense: Expense) => (
        <div className="text-right">
          <p className="font-semibold">{formatCurrency(expense.amount, 'HUF')}</p>
          {expense.vatAmount > 0 && (
            <p className="text-xs text-gray-500">ÁFA: {formatCurrency(expense.vatAmount, 'HUF')}</p>
          )}
        </div>
      ),
      className: 'text-right',
    },
    {
      key: 'isDeductible',
      header: 'Levonható',
      render: (expense: Expense) => (
        <span className={`inline-flex items-center justify-center w-6 h-6 rounded-full ${
          expense.isDeductible ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-400'
        }`}>
          {expense.isDeductible ? <Check className="w-4 h-4" /> : <X className="w-4 h-4" />}
        </span>
      ),
      className: 'text-center',
    },
    {
      key: 'actions',
      header: '',
      render: (expense: Expense) => (
        <div className="flex items-center justify-end gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onEdit(expense);
            }}
            className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
          >
            <Pencil className="w-4 h-4" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleDeleteClick(expense);
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
        data={expenses}
        columns={columns}
        keyExtractor={(expense) => expense.id}
        emptyMessage="Még nincs kiadás rögzítve"
      />

      <Modal
        isOpen={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        title="Kiadás törlése"
        size="sm"
      >
        <p className="text-gray-600 mb-6">
          Biztosan törölni szeretnéd ezt a kiadást?
          <br />
          <span className="font-medium">{selectedExpense?.description}</span>
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
