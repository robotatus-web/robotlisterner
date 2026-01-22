import { useEffect, useState } from 'react';
import { Plus } from 'lucide-react';
import { Header } from '../components/layout';
import { Button, Card, Modal } from '../components/common';
import { IncomeForm, IncomeList } from '../components/income';
import { useIncomeStore, useSettingsStore } from '../store';
import { Income } from '../types/income';
import { formatCurrency } from '../utils/formatters';

export function Incomes() {
  const { incomes, loadIncomes, addIncome, updateIncome, deleteIncome, getIncomesByYear, getTotalIncomeHUF, getTotalIncomeEUR } = useIncomeStore();
  const { selectedYear, loadSettings } = useSettingsStore();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingIncome, setEditingIncome] = useState<Income | null>(null);

  useEffect(() => {
    loadIncomes();
    loadSettings();
  }, [loadIncomes, loadSettings]);

  const yearIncomes = getIncomesByYear(selectedYear);
  const totalHUF = getTotalIncomeHUF(selectedYear);
  const totalEUR = getTotalIncomeEUR(selectedYear);

  const handleAdd = () => {
    setEditingIncome(null);
    setIsModalOpen(true);
  };

  const handleEdit = (income: Income) => {
    setEditingIncome(income);
    setIsModalOpen(true);
  };

  const handleSubmit = (data: Parameters<typeof addIncome>[0]) => {
    if (editingIncome) {
      updateIncome(editingIncome.id, data);
    } else {
      addIncome(data);
    }
    setIsModalOpen(false);
    setEditingIncome(null);
  };

  const handleDelete = (id: string) => {
    deleteIncome(id);
  };

  const sortedIncomes = [...yearIncomes].sort(
    (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
  );

  return (
    <div>
      <Header
        title="Bevételek"
        subtitle={`${yearIncomes.length} bevétel - ${selectedYear}`}
        action={
          <Button onClick={handleAdd}>
            <Plus className="w-4 h-4 mr-2" />
            Új bevétel
          </Button>
        }
      />

      <div className="p-8">
        {/* Summary cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card>
            <div className="text-center">
              <p className="text-sm text-gray-500">Összes bevétel (HUF)</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {formatCurrency(totalHUF, 'HUF')}
              </p>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <p className="text-sm text-gray-500">Összes bevétel (EUR)</p>
              <p className="text-2xl font-bold text-blue-600 mt-1">
                {formatCurrency(totalEUR, 'EUR')}
              </p>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <p className="text-sm text-gray-500">Tranzakciók száma</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {yearIncomes.length} db
              </p>
            </div>
          </Card>
        </div>

        {/* Income list */}
        <Card title="Bevételek listája">
          <IncomeList
            incomes={sortedIncomes}
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
          setEditingIncome(null);
        }}
        title={editingIncome ? 'Bevétel szerkesztése' : 'Új bevétel'}
        size="lg"
      >
        <IncomeForm
          onSubmit={handleSubmit}
          onCancel={() => {
            setIsModalOpen(false);
            setEditingIncome(null);
          }}
          initialData={editingIncome || undefined}
        />
      </Modal>
    </div>
  );
}
