import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/layout';
import { Dashboard, Incomes, Expenses, Invoices, TaxCalculator, Settings } from './pages';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/incomes" element={<Incomes />} />
          <Route path="/expenses" element={<Expenses />} />
          <Route path="/invoices" element={<Invoices />} />
          <Route path="/tax" element={<TaxCalculator />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
