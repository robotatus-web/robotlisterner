import { create } from 'zustand';
import { Expense, ExpenseFormData } from '../types/expense';
import { saveToStorage, loadFromStorage } from '../utils/storage';
import { generateId, getCurrentISODate } from '../utils/formatters';

interface ExpenseState {
  expenses: Expense[];
  isLoading: boolean;

  // Actions
  addExpense: (data: ExpenseFormData) => void;
  updateExpense: (id: string, data: Partial<ExpenseFormData>) => void;
  deleteExpense: (id: string) => void;
  loadExpenses: () => void;

  // Selectors
  getExpensesByYear: (year: number) => Expense[];
  getTotalExpenses: (year: number) => number;
  getDeductibleExpenses: (year: number) => number;
}

export const useExpenseStore = create<ExpenseState>((set, get) => ({
  expenses: [],
  isLoading: false,

  addExpense: (data) => {
    const now = getCurrentISODate();
    const newExpense: Expense = {
      ...data,
      id: generateId(),
      createdAt: now,
      updatedAt: now,
    };

    set((state) => {
      const newExpenses = [...state.expenses, newExpense];
      saveToStorage('expenses', newExpenses);
      return { expenses: newExpenses };
    });
  },

  updateExpense: (id, data) => {
    set((state) => {
      const newExpenses = state.expenses.map((expense) => {
        if (expense.id !== id) return expense;
        return { ...expense, ...data, updatedAt: getCurrentISODate() };
      });

      saveToStorage('expenses', newExpenses);
      return { expenses: newExpenses };
    });
  },

  deleteExpense: (id) => {
    set((state) => {
      const newExpenses = state.expenses.filter((expense) => expense.id !== id);
      saveToStorage('expenses', newExpenses);
      return { expenses: newExpenses };
    });
  },

  loadExpenses: () => {
    const expenses = loadFromStorage<Expense[]>('expenses', []);
    set({ expenses, isLoading: false });
  },

  getExpensesByYear: (year) => {
    return get().expenses.filter((expense) => {
      const expenseYear = new Date(expense.date).getFullYear();
      return expenseYear === year;
    });
  },

  getTotalExpenses: (year) => {
    return get()
      .getExpensesByYear(year)
      .reduce((sum, expense) => sum + expense.amount, 0);
  },

  getDeductibleExpenses: (year) => {
    return get()
      .getExpensesByYear(year)
      .filter((expense) => expense.isDeductible)
      .reduce((sum, expense) => sum + expense.amount, 0);
  },
}));
