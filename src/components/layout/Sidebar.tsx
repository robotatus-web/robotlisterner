import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  TrendingUp,
  TrendingDown,
  FileText,
  Calculator,
  Settings,
} from 'lucide-react';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Bevételek', href: '/incomes', icon: TrendingUp },
  { name: 'Kiadások', href: '/expenses', icon: TrendingDown },
  { name: 'Számlák', href: '/invoices', icon: FileText },
  { name: 'Adókalkulátor', href: '/tax', icon: Calculator },
  { name: 'Beállítások', href: '/settings', icon: Settings },
];

export function Sidebar() {
  return (
    <aside className="fixed inset-y-0 left-0 w-64 bg-gray-900 text-white">
      <div className="flex flex-col h-full">
        {/* Logo */}
        <div className="flex items-center h-16 px-6 border-b border-gray-800">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
              <Calculator className="w-5 h-5" />
            </div>
            <span className="text-lg font-bold">Könyvelő</span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-6 space-y-1">
          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                }`
              }
            >
              <item.icon className="w-5 h-5" />
              <span>{item.name}</span>
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-800">
          <p className="text-xs text-gray-500">
            Magyar Könyvelő App
          </p>
          <p className="text-xs text-gray-600 mt-1">
            SZJA szerinti adózás
          </p>
        </div>
      </div>
    </aside>
  );
}
