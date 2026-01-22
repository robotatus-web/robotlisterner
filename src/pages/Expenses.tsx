import { useEffect, useState } from 'react';
import { Plus } from 'lucide-react';
import { Header } from '../components/layout';
import { Button, Card, Modal } from '../components/common';
import { ExpenseForm, ExpenseList } from '../components/expense';
import { useExpenseStore, useSettingsStore } from '../store';
import { Expense } from '../types/expense';
import { formatCurrency } from '../utils/formatters';

export function Expenses() {
  const { expenses, loadExpenses, addExpense, updateExpense, deleteExpense, getExpensesByYear, getTotalExpenses, getDeductibleExpenses } = useExpenseStore();
  const { selectedYear, loadSettings } = useSettingsStore();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingExpense, setEditingExpense] = useState<Expense | null>(null);

  useEffect(() => {
    loadExpenses();
    loadSettings();
  }, [loadExpenses, loadSettings]);

  const yearExpenses = getExpensesByYear(selectedYear);
  const totalExpenses = getTotalExpenses(selectedYear);
  const deductibleExpenses = getDeductibleExpenses(selectedYear);

  const handleAdd = () => {
    setEditingExpense(null);
    setIsModalOpen(true);
  };

  const handleEdit = (expense: Expense) => {
    setEditingExpense(expense);
    setIsModalOpen(true);
  };

  const handleSubmit = (data: Parameters<typeof addExpense>[0]) => {
    if (editingExpense) {
      updateExpense(editingExpense.id, data);
    } else {
      addExpense(data);
    }
    setIsModalOpen(false);
    setEditingExpense(null);
  };

  const handleDelete = (id: string) => {
    deleteExpense(id);
  };

  const sortedExpenses = [...yearExpenses].sort(
    (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
  );

  return (
    <div>
      <Header
        title="Kiadások"
        subtitle={`${yearExpenses.length} kiadás - ${selectedYear}`}
        action={
          <Button onClick={handleAdd}>
            <Plus className="w-4 h-4 mr-2" />
            Új kiadás
          </Button>
        }
      />

      <div className="p-8">
        {/* Summary cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card>
            <div className="text-center">
              <p className="text-sm text-gray-500">Összes kiadás</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {formatCurrency(totalExpenses, 'HUF')}
              </p>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <p className="text-sm text-gray-500">Levonható kiadás</p>
              <p className="text-2xl font-bold text-green-600 mt-1">
                {formatCurrency(deductibleExpenses, 'HUF')}
              </p>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <p className="text-sm text-gray-500">Nem levonható</p>
              <p className="text-2xl font-bold text-red-600 mt-1">
                {formatCurrency(totalExpenses - deductibleExpenses, 'HUF')}
              </p>
            </div>
          </Card>
        </div>

        {/* Expense list */}
        <Card title="Kiadások listája">
          <ExpenseList
            expenses={sortedExpenses}
            onEdit={handleEdit}
            onDelete={handleDelete}
          />
        </Card>
      </div>

      {/* Add/Edit modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setEditingExpense(null);
        }}
        title={editingExpense ? 'Kiadás szerkesztése' : 'Új kiadás'}
        size="lg"
      >
        <ExpenseForm
          onSubmit={handleSubmit}
          onCancel={() => {
            setIsModalOpen(false);
            setEditingExpense(null);
          }}
          initialData={editingExpense || undefined}
        />
      </Modal>
    </div>
  );
}
