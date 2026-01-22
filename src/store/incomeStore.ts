import { create } from 'zustand';
import { Income, IncomeFormData } from '../types/income';
import { saveToStorage, loadFromStorage } from '../utils/storage';
import { generateId, getCurrentISODate } from '../utils/formatters';
import { convertEURtoHUF } from '../services/exchangeRate';

interface IncomeState {
  incomes: Income[];
  isLoading: boolean;

  // Actions
  addIncome: (data: IncomeFormData) => void;
  updateIncome: (id: string, data: Partial<IncomeFormData>) => void;
  deleteIncome: (id: string) => void;
  loadIncomes: () => void;

  // Selectors
  getIncomesByYear: (year: number) => Income[];
  getTotalIncomeHUF: (year: number) => number;
  getTotalIncomeEUR: (year: number) => number;
}

export const useIncomeStore = create<IncomeState>((set, get) => ({
  incomes: [],
  isLoading: false,

  addIncome: (data) => {
    const now = getCurrentISODate();
    const amountHUF = data.currency === 'EUR'
      ? convertEURtoHUF(data.amountOriginal, data.exchangeRate)
      : data.amountOriginal;

    const newIncome: Income = {
      ...data,
      id: generateId(),
      amountHUF,
      createdAt: now,
      updatedAt: now,
    };

    set((state) => {
      const newIncomes = [...state.incomes, newIncome];
      saveToStorage('incomes', newIncomes);
      return { incomes: newIncomes };
    });
  },

  updateIncome: (id, data) => {
    set((state) => {
      const newIncomes = state.incomes.map((income) => {
        if (income.id !== id) return income;

        const updated = { ...income, ...data, updatedAt: getCurrentISODate() };

        // Újraszámoljuk a HUF összeget ha változott a pénznem vagy összeg
        if (data.amountOriginal !== undefined || data.exchangeRate !== undefined || data.currency !== undefined) {
          const currency = data.currency ?? income.currency;
          const amount = data.amountOriginal ?? income.amountOriginal;
          const rate = data.exchangeRate ?? income.exchangeRate;
          updated.amountHUF = currency === 'EUR' ? convertEURtoHUF(amount, rate) : amount;
        }

        return updated;
      });

      saveToStorage('incomes', newIncomes);
      return { incomes: newIncomes };
    });
  },

  deleteIncome: (id) => {
    set((state) => {
      const newIncomes = state.incomes.filter((income) => income.id !== id);
      saveToStorage('incomes', newIncomes);
      return { incomes: newIncomes };
    });
  },

  loadIncomes: () => {
    const incomes = loadFromStorage<Income[]>('incomes', []);
    set({ incomes, isLoading: false });
  },

  getIncomesByYear: (year) => {
    return get().incomes.filter((income) => {
      const incomeYear = new Date(income.date).getFullYear();
      return incomeYear === year;
    });
  },

  getTotalIncomeHUF: (year) => {
    return get()
      .getIncomesByYear(year)
      .reduce((sum, income) => sum + income.amountHUF, 0);
  },

  getTotalIncomeEUR: (year) => {
    return get()
      .getIncomesByYear(year)
      .filter((income) => income.currency === 'EUR')
      .reduce((sum, income) => sum + income.amountOriginal, 0);
  },
}));
