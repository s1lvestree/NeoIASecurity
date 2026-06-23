import { useState, useMemo } from 'react';
import {
  Activity, ArrowDownRight, ArrowUpRight, Award, BarChart3,
  Download, Filter, Lock, RefreshCw, Search, Shield, TrendingUp, X,
} from 'lucide-react';
import {
  Area, AreaChart, CartesianGrid, Cell, PieChart, Pie,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';
import { useGovernance } from '../hooks/useGovernance';
import type { GovernanceReport } from '../types/governance';

function StateBadge({ state }: { state: string }) {
  const base = 'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium';
  if (state === 'Accepted')
    return (
      <span className={`${base} bg-emerald-950/60 text-emerald-400`}>
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
        Aceito
      </span>
    );
  if (state === 'Denied')
    return (
      <span className={`${base} bg-red-950/60 text-red-400`}>
        <span className="h-1.5 w-1.5 rounded-full bg-red-500" />
        Negado
      </span>
    );
  return (
    <span className={`${base} bg-amber-950/60 text-amber-400`}>
      <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
      Falhou
    </span>
  );
}

function MetricSkeleton() {
  return (
    <div className="animate-pulse rounded-xl border border-border bg-card p-5 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <div className="h-7 w-7 rounded-lg bg-muted" />
        <div className="h-3 w-10 rounded bg-muted" />
      </div>
      <div className="mb-2 h-3 w-24 rounded bg-muted" />
      <div className="mb-1 h-8 w-20 rounded bg-muted" />
      <div className="h-3 w-28 rounded bg-muted" />
    </div>
  );
}

function ReportModal({ markdown, onClose }: { markdown: string; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="flex max-h-[80vh] w-full max-w-3xl flex-col rounded-xl border border-border bg-card shadow-2xl">
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <h3 className="text-sm font-semibold text-foreground">Relatório Executivo de Governança</h3>
          <button onClick={onClose} className="text-muted-foreground transition-colors hover:text-foreground">
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-6">
          <pre className="font-mono text-xs leading-relaxed text-muted-foreground whitespace-pre-wrap">{markdown}</pre>
        </div>
        <div className="flex justify-end border-t border-border px-6 py-4">
          <button
            onClick={() => {
              const blob = new Blob([markdown], { type: 'text/markdown' });
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = 'relatorio-governanca.md';
              a.click();
              URL.revokeObjectURL(url);
            }}
            className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm text-primary-foreground transition-colors hover:bg-primary/90"
          >
            <Download className="h-4 w-4" />
            Baixar .md
          </button>
        </div>
      </div>
    </div>
  );
}

export function GovernancePage() {
  const { preview, loading, error, fetchReport, refresh } = useGovernance();
  const [report, setReport] = useState<GovernanceReport | null>(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [chartPeriod, setChartPeriod] = useState<'7D' | '30D' | '90D'>('7D');

  const handleExport = async () => {
    setReportLoading(true);
    const result = await fetchReport();
    setReportLoading(false);
    if (result) setReport(result);
  };

  const analysis = preview?.analysis;

  const eventTimelineData = useMemo(
    () =>
      Object.entries(preview?.events_per_day ?? {})
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([date, count]) => ({ time: date.slice(5), eventos: count as number })),
    [preview],
  );

  const stateDistribution = useMemo(() => {
    const rows = preview?.preview_rows ?? [];
    const counts = { accepted: 0, denied: 0, failed: 0 };
    rows.forEach((row) => {
      if (row.accessState === 'Accepted') counts.accepted++;
      else if (row.accessState === 'Denied') counts.denied++;
      else counts.failed++;
    });
    return [
      { name: 'Aceito', value: counts.accepted, color: '#10B981' },
      { name: 'Negado', value: counts.denied, color: '#EF4444' },
      { name: 'Falhou', value: counts.failed, color: '#F59E0B' },
    ].filter((d) => d.value > 0);
  }, [preview]);

  const filteredRows = useMemo(() => {
    const rows = preview?.preview_rows ?? [];
    if (!search) return rows;
    const q = search.toLowerCase();
    return rows.filter(
      (r) =>
        r.principalId?.toLowerCase().includes(q) ||
        r.applicationName?.toLowerCase().includes(q) ||
        r.accessState?.toLowerCase().includes(q),
    );
  }, [preview, search]);

  const metrics = [
    {
      label: 'TOTAL DE EVENTOS',
      value: analysis?.total_log_entries ?? 0,
      description: 'eventos processados',
      icon: Activity,
      trend: null,
    },
    {
      label: 'AUTENTICAÇÕES',
      value: analysis?.total_authentications ?? 0,
      description: 'tentativas registradas',
      icon: Shield,
      trend: null,
    },
    {
      label: 'ACESSO NEGADO',
      value: analysis?.denied_access_count ?? 0,
      description: 'bloqueios efetuados',
      icon: Lock,
      trend: analysis ? { value: `${analysis.denial_rate_pct.toFixed(1)}%`, up: false } : null,
    },
    {
      label: 'TAXA DE SUCESSO',
      value: analysis ? `${analysis.success_rate.toFixed(1)}%` : '—',
      description: 'índice de precisão',
      icon: TrendingUp,
      trend: analysis ? { value: `${analysis.success_rate.toFixed(1)}%`, up: true } : null,
    },
    {
      label: 'SCORE DE RISCO',
      value: analysis?.risk_score ?? 0,
      description: 'pontuação (0–100)',
      icon: Award,
      isRisk: true,
      trend: null,
    },
    {
      label: 'USUÁRIOS ÚNICOS',
      value: analysis?.unique_users_count ?? 0,
      description: 'identidades ativas',
      icon: BarChart3,
      trend: null,
    },
  ];

  return (
    <div className="space-y-6">
      {report && <ReportModal markdown={report.report_markdown} onClose={() => setReport(null)} />}

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="mb-1 text-2xl font-bold text-foreground">Governança IA</h2>
          <p className="text-sm text-muted-foreground">
            Análise de correlação e eventos de segurança em tempo real
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={refresh}
            className="flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-2 text-sm text-foreground shadow-sm transition-colors hover:bg-muted/40"
          >
            <RefreshCw className="h-4 w-4" />
            Atualizar
          </button>
          <button
            onClick={handleExport}
            disabled={reportLoading}
            className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-60"
          >
            <Download className="h-4 w-4" />
            {reportLoading ? 'Gerando...' : 'Exportar'}
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* Metric cards */}
      <div className="grid grid-cols-6 gap-4">
        {loading
          ? Array.from({ length: 6 }).map((_, i) => <MetricSkeleton key={i} />)
          : metrics.map((metric) => {
              const Icon = metric.icon;
              const isRisk = (metric as { isRisk?: boolean }).isRisk;
              const riskScore = isRisk ? (analysis?.risk_score ?? 0) : 0;
              const valueColor = isRisk
                ? riskScore >= 50
                  ? 'text-destructive'
                  : 'text-emerald-400'
                : 'text-foreground';

              return (
                <div key={metric.label} className="rounded-xl border border-border bg-card p-5 shadow-sm">
                  <div className="mb-3 flex items-start justify-between">
                    <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/10">
                      <Icon className="h-3.5 w-3.5 text-primary" />
                    </div>
                    {metric.trend && (
                      <div
                        className={`flex items-center gap-0.5 text-xs font-medium ${
                          metric.trend.up ? 'text-emerald-400' : 'text-destructive'
                        }`}
                      >
                        {metric.trend.up ? (
                          <ArrowUpRight className="h-3 w-3" />
                        ) : (
                          <ArrowDownRight className="h-3 w-3" />
                        )}
                        {metric.trend.value}
                      </div>
                    )}
                  </div>
                  <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    {metric.label}
                  </p>
                  <p className={`mb-1 text-2xl font-bold ${valueColor}`}>{metric.value}</p>
                  <p className="text-xs text-muted-foreground">{metric.description}</p>
                </div>
              );
            })}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-3 gap-4">
        {/* Events timeline */}
        <div className="col-span-2 rounded-xl border border-border bg-card p-6 shadow-sm">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-foreground">Linha do Tempo de Eventos</h3>
              <p className="mt-0.5 text-xs text-muted-foreground">Distribuição de eventos por dia</p>
            </div>
            <div className="flex gap-1 rounded-lg bg-muted/40 p-1">
              {(['7D', '30D', '90D'] as const).map((p) => (
                <button
                  key={p}
                  onClick={() => setChartPeriod(p)}
                  className={`rounded-md px-3 py-1 text-xs font-medium transition-colors ${
                    chartPeriod === p
                      ? 'bg-primary text-white shadow-sm'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
          <div className="h-52">
            {loading ? (
              <div className="h-full animate-pulse rounded-lg bg-muted/30" />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={eventTimelineData.length ? eventTimelineData : [{ time: '-', eventos: 0 }]}>
                  <defs>
                    <linearGradient id="eventsGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.2} />
                      <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                  <XAxis dataKey="time" stroke="#71717a" style={{ fontSize: '10px' }} tickLine={false} axisLine={false} />
                  <YAxis stroke="#71717a" style={{ fontSize: '10px' }} tickLine={false} axisLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#13141a',
                      border: '1px solid #1f2937',
                      borderRadius: '8px',
                      fontSize: '12px',
                      color: '#e8e9ed',
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="eventos"
                    stroke="#0ea5e9"
                    fill="url(#eventsGradient)"
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4, fill: '#0ea5e9' }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* State distribution */}
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
          <div className="mb-5">
            <h3 className="text-sm font-semibold text-foreground">Distribuição de Estados</h3>
            <p className="mt-0.5 text-xs text-muted-foreground">Acessos por tipo de resultado</p>
          </div>
          <div className="flex h-36 items-center justify-center">
            {loading ? (
              <div className="h-28 w-28 animate-pulse rounded-full bg-muted/30" />
            ) : stateDistribution.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={stateDistribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={38}
                    outerRadius={62}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {stateDistribution.map((entry, index) => (
                      <Cell key={index} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#13141a',
                      border: '1px solid #1f2937',
                      borderRadius: '8px',
                      fontSize: '12px',
                      color: '#e8e9ed',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-xs text-muted-foreground">Sem dados</p>
            )}
          </div>
          <div className="mt-3 space-y-2.5">
            {loading
              ? Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="h-2.5 w-2.5 rounded-full bg-muted animate-pulse" />
                      <div className="h-3 w-14 rounded bg-muted animate-pulse" />
                    </div>
                    <div className="h-3 w-6 rounded bg-muted animate-pulse" />
                  </div>
                ))
              : stateDistribution.map((item) => (
                  <div key={item.name} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                      <span className="text-xs text-muted-foreground">{item.name}</span>
                    </div>
                    <span className="text-xs font-semibold text-foreground">{item.value}</span>
                  </div>
                ))}
          </div>
        </div>
      </div>

      {/* Events table */}
      <div className="overflow-hidden rounded-xl border border-border bg-card shadow-sm">
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <h3 className="text-sm font-semibold text-foreground">Eventos de Segurança</h3>
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
              <input
                type="search"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Buscar..."
                className="w-48 rounded-lg border border-border bg-muted/30 py-1.5 pl-8 pr-3 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
            </div>
            <button className="flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:bg-muted/40">
              <Filter className="h-3.5 w-3.5" />
              Filtrar
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border bg-muted/20">
                {['Data/Hora', 'Usuário', 'Aplicação', 'Estado', 'Sinal de Risco', 'IP'].map((h) => (
                  <th key={h} className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading
                ? Array.from({ length: 8 }).map((_, i) => (
                    <tr key={i} className="border-b border-border">
                      {Array.from({ length: 6 }).map((_, j) => (
                        <td key={j} className="px-6 py-3.5">
                          <div className="h-4 w-24 animate-pulse rounded bg-muted" />
                        </td>
                      ))}
                    </tr>
                  ))
                : filteredRows.map((row, index) => (
                    <tr
                      key={index}
                      className="border-b border-border transition-colors last:border-0 hover:bg-muted/10"
                    >
                      <td className="px-6 py-3.5 font-mono text-xs text-muted-foreground">
                        {new Date(row.timestamp).toLocaleString('pt-BR')}
                      </td>
                      <td className="px-6 py-3.5 font-mono text-xs text-foreground">{row.principalId}</td>
                      <td className="px-6 py-3.5 text-sm text-foreground">{row.applicationName}</td>
                      <td className="px-6 py-3.5">
                        <StateBadge state={row.accessState} />
                      </td>
                      <td className="px-6 py-3.5 text-xs">
                        {row.riskSignal === 'OK' ? (
                          <span className="font-medium text-emerald-400">OK</span>
                        ) : (
                          <span className="font-medium text-amber-400">{row.riskSignal}</span>
                        )}
                      </td>
                      <td className="px-6 py-3.5 font-mono text-xs text-muted-foreground">{row.source_ip}</td>
                    </tr>
                  ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
