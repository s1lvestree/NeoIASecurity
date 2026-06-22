import { LucideIcon, TrendingDown, TrendingUp } from 'lucide-react';

interface MetricCardProps {
  icon: LucideIcon;
  label: string;
  value: string;
  change: string;
  trend: 'up' | 'down';
}

export function MetricCard({ icon: Icon, label, value, change, trend }: MetricCardProps) {
  return (
    <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
      <div className="flex items-start justify-between mb-4">
        <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
          <Icon className="w-5 h-5 text-primary" />
        </div>
        <div className="flex items-center gap-1">
          {trend === 'up' ? (
            <TrendingUp className="w-3 h-3 text-primary" />
          ) : (
            <TrendingDown className="w-3 h-3 text-destructive" />
          )}
          <span className={`text-xs font-medium ${trend === 'up' ? 'text-primary' : 'text-destructive'}`}>
            {change}
          </span>
        </div>
      </div>
      <div>
        <p className="text-2xl font-semibold text-foreground mb-1">{value}</p>
        <p className="text-sm text-muted-foreground">{label}</p>
      </div>
    </div>
  );
}
