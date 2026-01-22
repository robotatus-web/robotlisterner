import { useSettingsStore } from '../../store';
import { Select } from '../common';

const years = [2024, 2025, 2026].map((year) => ({
  value: String(year),
  label: String(year),
}));

interface HeaderProps {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
}

export function Header({ title, subtitle, action }: HeaderProps) {
  const { selectedYear, setSelectedYear } = useSettingsStore();

  return (
    <header className="bg-white border-b border-gray-200 px-8 py-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
          {subtitle && (
            <p className="mt-1 text-sm text-gray-500">{subtitle}</p>
          )}
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">Év:</span>
            <Select
              options={years}
              value={String(selectedYear)}
              onChange={(e) => setSelectedYear(Number(e.target.value))}
              className="w-24"
            />
          </div>
          {action}
        </div>
      </div>
    </header>
  );
}
