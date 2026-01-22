export interface BusinessSettings {
  businessName: string;
  taxNumber: string;           // Adószám
  address: string;
  bankAccount: string;

  // Adózási beállítások
  taxYear: number;
  vatPayer: boolean;           // ÁFA alany-e

  // EUR beállítások
  defaultCurrency: 'EUR' | 'HUF';
  defaultCustomerCountry: string;
}

export interface AppSettings {
  business: BusinessSettings;
  displayCurrency: 'EUR' | 'HUF' | 'both';
  language: 'hu';
  theme: 'light' | 'dark' | 'system';
}

export const DEFAULT_SETTINGS: AppSettings = {
  business: {
    businessName: '',
    taxNumber: '',
    address: '',
    bankAccount: '',
    taxYear: new Date().getFullYear(),
    vatPayer: false,
    defaultCurrency: 'EUR',
    defaultCustomerCountry: '',
  },
  displayCurrency: 'both',
  language: 'hu',
  theme: 'light',
};
