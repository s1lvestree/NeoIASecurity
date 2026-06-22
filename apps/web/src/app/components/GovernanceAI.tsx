import { AlertTriangle, TrendingUp, Clock, Activity, CheckCircle2 } from 'lucide-react';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useGovernance } from '../hooks/useGovernance';
import type { GovernanceRecommendation } from '../types/governance';

function priorityToSeverity(priority: string): 'critical' | 'high' | 'warning' | 'info' {
  if (priority === 'Alta') return 'critical';
  if (priority === 'Média') return 'high';
  if (priority === 'Baixa') return 'warning';
  return 'info';
}

function InsightCard({ rec, index }: { rec: GovernanceRecommendation; index: number }) {
  const severity = priorityToSeverity(rec.priority);
  const severityStyles = {
    critical: { bg: 'bg-destructive/10', icon: 'text-destructive', badge: 'bg-destructive/10 text-destructive' },
    high: { bg: 'bg-amber-500/10', icon: 'text-amber-500', badge: 'bg-amber-500/10 text-amber-500' },
    warning: { bg: 'bg-blue-500/10', icon: 'text-blue-500', badge: 'bg-blue-500/10 text-blue-500' },
    info: { bg: 'bg-primary/10', icon: 'text-primary', badge: 'bg-primary/10 text-primary' },
  }[severity];

  const timeLabels = ['2 min atrás', '15 min atrás', '1 hora atrás', '2 horas atrás'];

  return (
    <div className="bg-muted/20 border border-border rounded-lg p-4 hover:bg-muted/30 transition-colors">
      <div className="flex items-start gap-3">
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${severityStyles.bg}`}>
          {severity === 'critical' || severity === 'high' ? (
            <AlertTriangle className={`w-4 h-4 ${severityStyles.icon}`} />
          ) : (
            <TrendingUp className={`w-4 h-4 ${severityStyles.icon}`} />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <h5 className="text-sm font-semibold text-foreground">{rec.policy_name}</h5>
            <span className={`text-xs px-2 py-0.5 rounded-full ${severityStyles.badge}`}>
              {rec.priority.toUpperCase()}
            </span>
          </div>
          <p className="text-xs text-muted-foreground mb-1">{rec.scenario_or_condition}</p>
          <p className="text-xs text-foreground/70 mb-2">{rec.recommended_decision}</p>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Clock className="w-3 h-3" />
              <span>{timeLabels[index % timeLabels.length]}</span>
            </div>
            <span className="text-xs text-primary/70">Logs STA</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export function GovernanceAI() {
  const { preview, loading } = useGovernance();

  const riskScore = preview?.risk_score ?? 75;
  const analysis = preview?.analysis;

  const eventTimelineData = Object.entries(preview?.events_per_day ?? {})
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, count]) => ({
      time: date.slice(5),
      events: count,
    }));

  const riskTrendData = eventTimelineData.map((point, i) => ({
    time: point.time,
    score: Math.min(100, Math.max(0,
      Math.round((analysis?.denial_rate_pct ?? 15) * 0.6 +
        (analysis?.failure_rate_pct ?? 10) * 0.2 +
        (i % 3 === 0 ? 5 : -3))
    )),
  }));

  return (
    <div className="flex flex-col h-full bg-card border border-border rounded-xl overflow-hidden">
      <div className="px-6 py-4 border-b border-border bg-card/50 backdrop-blur-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-destructive/10 rounded-lg flex items-center justify-center">
              <Activity className="w-4 h-4 text-destructive" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-foreground">Governança IA</h3>
              <p className="text-xs text-muted-foreground">Dashboard executivo de segurança</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">Score de Risco:</span>
              <span className={`text-lg font-bold ${riskScore >= 50 ? 'text-destructive' : 'text-emerald-400'}`}>
                {loading ? '—' : `${riskScore}/100`}
              </span>
            </div>
            <div className="flex items-center gap-1.5 px-2 py-1 bg-primary/10 rounded-md">
              <CheckCircle2 className="w-3 h-3 text-primary" />
              <span className="text-xs text-primary">Dados Mascarados</span>
            </div>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        <div>
          <h4 className="text-xs font-semibold text-muted-foreground mb-3 uppercase tracking-wide">
            Tendência de Risco (período)
          </h4>
          <div className="h-40 bg-muted/20 rounded-lg p-4">
            {loading ? (
              <div className="h-full flex items-center justify-center">
                <div className="w-full h-full bg-muted rounded animate-pulse" />
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={riskTrendData.length ? riskTrendData : [{ time: '-', score: 0 }]}>
                  <defs>
                    <linearGradient id="riskGradient-governance-ai" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                  <XAxis dataKey="time" stroke="#71717a" style={{ fontSize: '10px' }} />
                  <YAxis stroke="#71717a" style={{ fontSize: '10px' }} domain={[0, 100]} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#13141a',
                      border: '1px solid #1f2937',
                      borderRadius: '8px',
                      fontSize: '12px',
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="score"
                    stroke="#ef4444"
                    fill="url(#riskGradient-governance-ai)"
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        <div>
          <h4 className="text-xs font-semibold text-muted-foreground mb-3 uppercase tracking-wide">
            Linha do Tempo de Eventos
          </h4>
          <div className="h-40 bg-muted/20 rounded-lg p-4">
            {loading ? (
              <div className="h-full bg-muted rounded animate-pulse" />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={eventTimelineData.length ? eventTimelineData : [{ time: '-', events: 0 }]}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                  <XAxis dataKey="time" stroke="#71717a" style={{ fontSize: '10px' }} />
                  <YAxis stroke="#71717a" style={{ fontSize: '10px' }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#13141a',
                      border: '1px solid #1f2937',
                      borderRadius: '8px',
                      fontSize: '12px',
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="events"
                    stroke="#0ea5e9"
                    strokeWidth={2}
                    dot={{ fill: '#0ea5e9', r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        <div>
          <h4 className="text-xs font-semibold text-muted-foreground mb-3 uppercase tracking-wide">
            Insights e Recomendações da IA
          </h4>
          {loading ? (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="h-20 bg-muted rounded-lg animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="space-y-3">
              {(preview?.recommendations ?? []).map((rec, index) => (
                <InsightCard key={index} rec={rec} index={index} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
