import { VatStatus } from './income';

export type InvoiceStatus =
  | 'draft'      // Piszkozat
  | 'issued'     // Kiállított
  | 'paid'       // Fizetve
  | 'overdue'    // Lejárt
  | 'cancelled'; // Sztornózott

export interface InvoiceItem {
  id: string;
  description: string;
  quantity: number;
  unitPrice: number;      // EUR
  amount: number;         // quantity * unitPrice
}

export interface Invoice {
  id: string;
  invoiceNumber: string;
  issueDate: string;       // Kiállítás dátuma
  deliveryDate: string;    // Teljesítés dátuma
  dueDate: string;         // Fizetési határidő
  customerName: string;
  customerAddress: string;
  customerCountry: string;
  customerTaxNumber?: string;
  items: InvoiceItem[];
  currency: 'EUR' | 'HUF';
  subtotal: number;        // Nettó összeg
  vatRate: number;         // ÁFA kulcs (0, 5, 27)
  vatAmount: number;       // ÁFA összeg
  total: number;           // Bruttó összeg
  vatStatus: VatStatus;
  exchangeRate: number;    // MNB árfolyam
  totalHUF: number;        // HUF összeg
  status: InvoiceStatus;
  paidDate?: string;
  notes?: string;
  createdAt: string;
  updatedAt: string;
}

export type InvoiceFormData = Omit<Invoice, 'id' | 'createdAt' | 'updatedAt'>;
