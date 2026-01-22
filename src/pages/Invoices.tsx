import { useEffect } from 'react';
import { FileText, Plus } from 'lucide-react';
import { Header } from '../components/layout';
import { Button, Card } from '../components/common';
import { useSettingsStore } from '../store';

export function Invoices() {
  const { selectedYear, loadSettings } = useSettingsStore();

  useEffect(() => {
    loadSettings();
  }, [loadSettings]);

  return (
    <div>
      <Header
        title="Számlák"
        subtitle={`Számla nyilvántartás - ${selectedYear}`}
        action={
          <Button disabled>
            <Plus className="w-4 h-4 mr-2" />
            Új számla
          </Button>
        }
      />

      <div className="p-8">
        <Card>
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <FileText className="w-8 h-8 text-gray-400" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Számla modul fejlesztés alatt
            </h3>
            <p className="text-gray-500 max-w-md mx-auto">
              A számlázási funkció hamarosan elérhető lesz. Addig is használd a bevételek
              oldalt a bevételeid nyilvántartására.
            </p>
          </div>
        </Card>

        {/* Feature preview */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <div className="text-center p-4">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <FileText className="w-6 h-6 text-blue-600" />
              </div>
              <h4 className="font-medium text-gray-900">Számla készítés</h4>
              <p className="text-sm text-gray-500 mt-1">
                EUR számlák készítése EU-n kívüli ügyfeleknek
              </p>
            </div>
          </Card>
          <Card>
            <div className="text-center p-4">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <FileText className="w-6 h-6 text-green-600" />
              </div>
              <h4 className="font-medium text-gray-900">Automatikus MNB árfolyam</h4>
              <p className="text-sm text-gray-500 mt-1">
                Árfolyam lekérés a teljesítés napjára
              </p>
            </div>
          </Card>
          <Card>
            <div className="text-center p-4">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <FileText className="w-6 h-6 text-purple-600" />
              </div>
              <h4 className="font-medium text-gray-900">PDF export</h4>
              <p className="text-sm text-gray-500 mt-1">
                Számlák exportálása PDF formátumban
              </p>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
