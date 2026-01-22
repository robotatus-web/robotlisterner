import { create } from 'zustand';
import { AppSettings, DEFAULT_SETTINGS } from '../types/settings';
import { saveToStorage, loadFromStorage } from '../utils/storage';

interface SettingsState {
  settings: AppSettings;
  selectedYear: number;

  // Actions
  updateSettings: (settings: Partial<AppSettings>) => void;
  updateBusinessSettings: (settings: Partial<AppSettings['business']>) => void;
  setSelectedYear: (year: number) => void;
  loadSettings: () => void;
  resetSettings: () => void;
}

export const useSettingsStore = create<SettingsState>((set, get) => ({
  settings: DEFAULT_SETTINGS,
  selectedYear: new Date().getFullYear(),

  updateSettings: (newSettings) => {
    set((state) => {
      const updated = { ...state.settings, ...newSettings };
      saveToStorage('settings', updated);
      return { settings: updated };
    });
  },

  updateBusinessSettings: (businessSettings) => {
    set((state) => {
      const updated = {
        ...state.settings,
        business: { ...state.settings.business, ...businessSettings },
      };
      saveToStorage('settings', updated);
      return { settings: updated };
    });
  },

  setSelectedYear: (year) => {
    set({ selectedYear: year });
    saveToStorage('selectedYear', year);
  },

  loadSettings: () => {
    const settings = loadFromStorage<AppSettings>('settings', DEFAULT_SETTINGS);
    const selectedYear = loadFromStorage<number>('selectedYear', new Date().getFullYear());
    set({ settings, selectedYear });
  },

  resetSettings: () => {
    set({ settings: DEFAULT_SETTINGS });
    saveToStorage('settings', DEFAULT_SETTINGS);
  },
}));
