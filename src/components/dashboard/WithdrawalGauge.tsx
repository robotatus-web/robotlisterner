interface WithdrawalGaugeProps {
  percentage: number;
  netAmount: number;
  grossAmount: number;
}

export function WithdrawalGauge({ percentage, netAmount, grossAmount }: WithdrawalGaugeProps) {
  const clampedPercentage = Math.min(100, Math.max(0, percentage));
  const circumference = 2 * Math.PI * 45;
  const strokeDashoffset = circumference - (clampedPercentage / 100) * circumference;

  const getColor = () => {
    if (percentage >= 70) return '#22c55e'; // green
    if (percentage >= 50) return '#eab308'; // yellow
    return '#ef4444'; // red
  };

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-32 h-32">
        <svg className="w-32 h-32 transform -rotate-90">
          {/* Background circle */}
          <circle
            cx="64"
            cy="64"
            r="45"
            stroke="#e5e7eb"
            strokeWidth="10"
            fill="none"
          />
          {/* Progress circle */}
          <circle
            cx="64"
            cy="64"
            r="45"
            stroke={getColor()}
            strokeWidth="10"
            fill="none"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            className="transition-all duration-500"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-2xl font-bold" style={{ color: getColor() }}>
            {percentage.toFixed(0)}%
          </span>
        </div>
      </div>
      <div className="mt-4 text-center">
        <p className="text-sm text-gray-500">Kivehető arány</p>
        <p className="text-lg font-semibold text-gray-900">
          {netAmount.toLocaleString('hu-HU')} Ft
        </p>
        <p className="text-xs text-gray-400">
          / {grossAmount.toLocaleString('hu-HU')} Ft bevételből
        </p>
      </div>
    </div>
  );
}
