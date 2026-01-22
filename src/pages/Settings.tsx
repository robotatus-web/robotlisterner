import { useEffect } from 'react';
import { Header } from '../components/layout';
import { Card, Input, Button } from '../components/common';
import { useSettingsStore } from '../store';
import { getMinimumWage } from '../services/taxCalculator';
import { formatCurrency } from '../utils/formatters';

export function Settings() {
  const { settings, selectedYear, updateBusinessSettings, loadSettings } = useSettingsStore();

  useEffect(() => {
    loadSettings();
  }, [loadSettings]);

  const minimumWage = getMinimumWage(selectedYear);

  return (
    <div>
      <Header
        title="Beállítások"
        subtitle="Vállalkozási és alkalmazás beállítások"
      />

      <div className="p-8 max-w-3xl">
        {/* Vállalkozás adatai */}
        <Card title="Vállalkozás adatai" className="mb-6">
          <div className="space-y-4">
            <Input
              label="Vállalkozás neve"
              value={settings.business.businessName}
              onChange={(e) => updateBusinessSettings({ businessName: e.target.value })}
              placeholder="Pl. Kiss János EV"
            />
            <Input
              label="Adószám"
              value={settings.business.taxNumber}
              onChange={(e) => updateBusinessSettings({ taxNumber: e.target.value })}
              placeholder="Pl. 12345678-1-42"
            />
            <Input
              label="Cím"
              value={settings.business.address}
              onChange={(e) => updateBusinessSettings({ address: e.target.value })}
              placeholder="Pl. 1234 Budapest, Példa utca 1."
            />
            <Input
              label="Bankszámlaszám"
              value={settings.business.bankAccount}
              onChange={(e) => updateBusinessSettings({ bankAccount: e.target.value })}
              placeholder="Pl. 12345678-12345678-12345678"
            />
          </div>
        </Card>

        {/* Adózási információk */}
        <Card title="Adózási információk" className="mb-6">
          <div className="space-y-4">
            <div className="p-4 bg-blue-50 rounded-lg">
              <h4 className="font-medium text-blue-900">Adózási mód</h4>
              <p className="text-blue-700 mt-1">SZJA szerinti adózás (tételes költségelszámolás)</p>
              <p className="text-sm text-blue-600 mt-2">
                A bevételből levonhatod a ténylegesen felmerült, igazolt üzleti költségeket.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">Aktuális év</p>
                <p className="text-xl font-bold">{selectedYear}</p>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">Minimálbér ({selectedYear})</p>
                <p className="text-xl font-bold">{formatCurrency(minimumWage, 'HUF')}/hó</p>
              </div>
            </div>

            <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
              <input
                type="checkbox"
                id="vatPayer"
                checked={settings.business.vatPayer}
                onChange={(e) => updateBusinessSettings({ vatPayer: e.target.checked })}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label htmlFor="vatPayer" className="text-gray-700">
                ÁFA alany vagyok
              </label>
            </div>
          </div>
        </Card>

        {/* EUR beállítások */}
        <Card title="EUR bevétel beállítások" className="mb-6">
          <div className="space-y-4">
            <Input
              label="Alapértelmezett ügyfél országa"
              value={settings.business.defaultCustomerCountry}
              onChange={(e) => updateBusinessSettings({ defaultCustomerCountry: e.target.value })}
              placeholder="Pl. USA"
              helperText="EU-n kívüli ország a 0% ÁFA alkalmazásához"
            />

            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <h4 className="font-medium text-yellow-900">Fontos tudnivalók</h4>
              <ul className="text-sm text-yellow-800 mt-2 space-y-1 list-disc list-inside">
                <li>EU-n kívüli szolgáltatás export: 0% ÁFA</li>
                <li>MNB árfolyam a teljesítés napján</li>
                <li>Számlán fel kell tüntetni: "Fordított adózás" vagy "Áfa tv. 37.§"</li>
              </ul>
            </div>
          </div>
        </Card>

        {/* Adatok kezelése */}
        <Card title="Adatok kezelése">
          <div className="space-y-4">
            <p className="text-sm text-gray-500">
              Az adatok a böngésző helyi tárhelyén (localStorage) tárolódnak.
              Böngésző adatok törlése esetén elveszhetnek.
            </p>

            <div className="flex gap-3">
              <Button
                variant="secondary"
                onClick={() => {
                  const data = {
                    incomes: localStorage.getItem('accounting_incomes'),
                    expenses: localStorage.getItem('accounting_expenses'),
                    settings: localStorage.getItem('accounting_settings'),
                  };
                  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `konyvelo-backup-${new Date().toISOString().split('T')[0]}.json`;
                  a.click();
                }}
              >
                Adatok exportálása
              </Button>
              <Button
                variant="ghost"
                onClick={() => {
                  const input = document.createElement('input');
                  input.type = 'file';
                  input.accept = '.json';
                  input.onchange = (e) => {
                    const file = (e.target as HTMLInputElement).files?.[0];
                    if (file) {
                      const reader = new FileReader();
                      reader.onload = (e) => {
                        try {
                          const data = JSON.parse(e.target?.result as string);
                          if (data.incomes) localStorage.setItem('accounting_incomes', data.incomes);
                          if (data.expenses) localStorage.setItem('accounting_expenses', data.expenses);
                          if (data.settings) localStorage.setItem('accounting_settings', data.settings);
                          window.location.reload();
                        } catch {
                          alert('Hibás fájl formátum');
                        }
                      };
                      reader.readAsText(file);
                    }
                  };
                  input.click();
                }}
              >
                Adatok importálása
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
