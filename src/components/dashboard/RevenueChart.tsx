import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

interface MonthlyData {
  month: string;
  income: number;
  expense: number;
}

interface RevenueChartProps {
  data: MonthlyData[];
}

const monthNames = [
  'Jan', 'Feb', 'Már', 'Ápr', 'Máj', 'Jún',
  'Júl', 'Aug', 'Szep', 'Okt', 'Nov', 'Dec'
];

export function RevenueChart({ data }: RevenueChartProps) {
  const chartData = data.map((item, index) => ({
    ...item,
    month: monthNames[index] || item.month,
  }));

  const formatValue = (value: number) => {
    if (value >= 1000000) {
      return `${(value / 1000000).toFixed(1)}M`;
    }
    if (value >= 1000) {
      return `${(value / 1000).toFixed(0)}k`;
    }
    return value.toString();
  };

  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="month"
            tick={{ fill: '#6b7280', fontSize: 12 }}
            axisLine={{ stroke: '#e5e7eb' }}
          />
          <YAxis
            tickFormatter={formatValue}
            tick={{ fill: '#6b7280', fontSize: 12 }}
            axisLine={{ stroke: '#e5e7eb' }}
          />
          <Tooltip
            formatter={(value) => [
              `${Number(value).toLocaleString('hu-HU')} Ft`,
            ]}
            labelStyle={{ color: '#111827' }}
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
            }}
          />
          <Legend />
          <Bar
            dataKey="income"
            name="Bevétel"
            fill="#3b82f6"
            radius={[4, 4, 0, 0]}
          />
          <Bar
            dataKey="expense"
            name="Kiadás"
            fill="#ef4444"
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
