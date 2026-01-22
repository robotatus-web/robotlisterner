export type ExpenseCategory =
  | 'office'           // Iroda (bérlés, rezsi)
  | 'equipment'        // Eszközök (laptop, monitor)
  | 'software'         // Szoftverek, előfizetések
  | 'professional'     // Szakmai szolgáltatások (könyvelő, ügyvéd)
  | 'travel'           // Utazás, szállás
  | 'education'        // Képzés, szakkönyvek
  | 'bank'             // Bank költségek
  | 'marketing'        // Marketing, reklám
  | 'telecom'          // Telefon, internet
  | 'insurance'        // Biztosítás
  | 'other';           // Egyéb

export interface Expense {
  id: string;
  date: string;              // Költség dátuma (ISO string)
  description: string;
  category: ExpenseCategory;
  amount: number;            // Bruttó összeg HUF
  vatAmount: number;         // ÁFA összeg (ha visszaigényelhető)
  netAmount: number;         // Nettó összeg
  isDeductible: boolean;     // Adóból levonható-e
  receiptNumber?: string;    // Bizonylat száma
  vendor?: string;           // Szállító neve
  notes?: string;
  createdAt: string;
  updatedAt: string;
}

export type ExpenseFormData = Omit<Expense, 'id' | 'createdAt' | 'updatedAt'>;

export const EXPENSE_CATEGORY_LABELS: Record<ExpenseCategory, string> = {
  office: 'Iroda (bérlés, rezsi)',
  equipment: 'Eszközök',
  software: 'Szoftverek',
  professional: 'Szakmai szolgáltatások',
  travel: 'Utazás, szállás',
  education: 'Képzés, könyvek',
  bank: 'Bank költségek',
  marketing: 'Marketing',
  telecom: 'Telefon, internet',
  insurance: 'Biztosítás',
  other: 'Egyéb',
};
