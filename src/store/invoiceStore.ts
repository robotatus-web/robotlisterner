import { create } from 'zustand';
import { Invoice, InvoiceFormData } from '../types/invoice';
import { saveToStorage, loadFromStorage } from '../utils/storage';
import { generateId, getCurrentISODate } from '../utils/formatters';

interface InvoiceState {
  invoices: Invoice[];
  isLoading: boolean;

  // Actions
  addInvoice: (data: InvoiceFormData) => void;
  updateInvoice: (id: string, data: Partial<InvoiceFormData>) => void;
  deleteInvoice: (id: string) => void;
  markAsPaid: (id: string, paidDate: string) => void;
  loadInvoices: () => void;

  // Selectors
  getInvoicesByYear: (year: number) => Invoice[];
  getInvoicesByStatus: (status: Invoice['status']) => Invoice[];
  getNextInvoiceNumber: (year: number) => string;
}

export const useInvoiceStore = create<InvoiceState>((set, get) => ({
  invoices: [],
  isLoading: false,

  addInvoice: (data) => {
    const now = getCurrentISODate();
    const newInvoice: Invoice = {
      ...data,
      id: generateId(),
      createdAt: now,
      updatedAt: now,
    };

    set((state) => {
      const newInvoices = [...state.invoices, newInvoice];
      saveToStorage('invoices', newInvoices);
      return { invoices: newInvoices };
    });
  },

  updateInvoice: (id, data) => {
    set((state) => {
      const newInvoices = state.invoices.map((invoice) => {
        if (invoice.id !== id) return invoice;
        return { ...invoice, ...data, updatedAt: getCurrentISODate() };
      });

      saveToStorage('invoices', newInvoices);
      return { invoices: newInvoices };
    });
  },

  deleteInvoice: (id) => {
    set((state) => {
      const newInvoices = state.invoices.filter((invoice) => invoice.id !== id);
      saveToStorage('invoices', newInvoices);
      return { invoices: newInvoices };
    });
  },

  markAsPaid: (id, paidDate) => {
    set((state) => {
      const newInvoices = state.invoices.map((invoice) => {
        if (invoice.id !== id) return invoice;
        return {
          ...invoice,
          status: 'paid' as const,
          paidDate,
          updatedAt: getCurrentISODate(),
        };
      });

      saveToStorage('invoices', newInvoices);
      return { invoices: newInvoices };
    });
  },

  loadInvoices: () => {
    const invoices = loadFromStorage<Invoice[]>('invoices', []);
    set({ invoices, isLoading: false });
  },

  getInvoicesByYear: (year) => {
    return get().invoices.filter((invoice) => {
      const invoiceYear = new Date(invoice.issueDate).getFullYear();
      return invoiceYear === year;
    });
  },

  getInvoicesByStatus: (status) => {
    return get().invoices.filter((invoice) => invoice.status === status);
  },

  getNextInvoiceNumber: (year) => {
    const yearInvoices = get().getInvoicesByYear(year);
    const nextNumber = yearInvoices.length + 1;
    return `INV-${year}-${String(nextNumber).padStart(4, '0')}`;
  },
}));
