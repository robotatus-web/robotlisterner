export type Currency = 'EUR' | 'HUF';

export type IncomeCategory =
  | 'service'      // Szolgáltatás
  | 'product'      // Termék értékesítés
  | 'consulting'   // Konzultáció
  | 'royalty'      // Jogdíj
  | 'other';       // Egyéb

export type VatStatus =
  | 'domestic'           // Belföldi ÁFÁ-s
  | 'eu_reverse_charge'  // EU fordított adózás
  | 'non_eu_export';     // EU-n kívüli export (0%)

export interface Income {
  id: string;
  date: string;              // Teljesítés dátuma (ISO string)
  description: string;
  category: IncomeCategory;
  currency: Currency;
  amountOriginal: number;    // Eredeti összeg (EUR vagy HUF)
  exchangeRate: number;      // MNB árfolyam (1 ha HUF)
  amountHUF: number;         // HUF összeg
  customerName: string;
  customerCountry: string;
  invoiceNumber?: string;
  vatStatus: VatStatus;
  notes?: string;
  createdAt: string;
  updatedAt: string;
}

export type IncomeFormData = Omit<Income, 'id' | 'amountHUF' | 'createdAt' | 'updatedAt'>;
