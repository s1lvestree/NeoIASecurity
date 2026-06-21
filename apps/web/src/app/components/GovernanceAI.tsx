import { AlertTriangle, TrendingUp, Clock, Activity, CheckCircle2 } from 'lucide-react';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const riskData = [
  { time: '00:00', score: 45 },
  { time: '04:00', score: 38 },
  { time: '08:00', score: 52 },
  { time: '12:00', score: 68 },
  { time: '16:00', score: 75 },
  { time: '20:00', score: 62 },
];

const eventData = [
  { time: '00:00', events: 120 },
  { time: '04:00', events: 80 },
  { time: '08:00', events: 240 },
  { time: '12:00', events: 380 },
  { time: '16:00', events: 420 },
  { time: '20:00', events: 280 },
];

const insights = [
  {
    severity: 'critical',
    title: 'STA: 32 eventos críticos de autenticação',
    description: 'Múltiplas negações de MFA e tentativas de acesso não autorizado de locais incomuns',
    time: '2 min atrás',
    source: 'Logs STA',
  },
  {
    severity: 'high',
    title: 'DLP/Safetica: 4 usuários de alto risco',
    description: 'Usuários com violações repetidas de política, tentativas de transferência de dados e operações não autorizadas',
    time: '15 min atrás',
    source: 'DLP/Safetica',
  },
  {
    severity: 'warning',
    title: 'IAM: Acessos fora do horário comercial',
    description: '18 instâncias de acesso a dados sensíveis após o expediente detectadas pelos sistemas IAM/PAM',
    time: '1 hora atrás',
    source: 'IAM/PAM',
  },
  {
    severity: 'info',
    title: 'Octadesk: Criação de chamado recomendada',
    description: 'IA recomenda criar 3 incidentes de segurança baseados em padrões detectados. Revisão humana necessária.',
    time: '2 horas atrás',
    source: 'Análise IA',
  },
];

export function GovernanceAI() {
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
              <span className="text-lg font-bold text-destructive">75/100</span>
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
            Tendência de Risco (24h)
          </h4>
          <div className="h-40 bg-muted/20 rounded-lg p-4">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={riskData}>
                <defs>
                  <linearGradient id="riskGradient-governance-ai" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                  </linearGradient>
                </defs>
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
                <Area
                  type="monotone"
                  dataKey="score"
                  stroke="#ef4444"
                  fill="url(#riskGradient-governance-ai)"
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div>
          <h4 className="text-xs font-semibold text-muted-foreground mb-3 uppercase tracking-wide">
            Linha do Tempo de Eventos
          </h4>
          <div className="h-40 bg-muted/20 rounded-lg p-4">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={eventData}>
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
          </div>
        </div>

        <div>
          <h4 className="text-xs font-semibold text-muted-foreground mb-3 uppercase tracking-wide">
            Insights e Recomendações da IA
          </h4>
          <div className="space-y-3">
            {insights.map((insight, index) => (
              <div
                key={index}
                className="bg-muted/20 border border-border rounded-lg p-4 hover:bg-muted/30 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <div
                    className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                      insight.severity === 'critical'
                        ? 'bg-destructive/10'
                        : insight.severity === 'high'
                        ? 'bg-amber-500/10'
                        : insight.severity === 'warning'
                        ? 'bg-blue-500/10'
                        : 'bg-primary/10'
                    }`}
                  >
                    {insight.severity === 'critical' || insight.severity === 'high' ? (
                      <AlertTriangle
                        className={`w-4 h-4 ${
                          insight.severity === 'critical' ? 'text-destructive' : 'text-amber-500'
                        }`}
                      />
                    ) : (
                      <TrendingUp className={`w-4 h-4 ${insight.severity === 'warning' ? 'text-blue-500' : 'text-primary'}`} />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <h5 className="text-sm font-semibold text-foreground">{insight.title}</h5>
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full ${
                          insight.severity === 'critical'
                            ? 'bg-destructive/10 text-destructive'
                            : insight.severity === 'high'
                            ? 'bg-amber-500/10 text-amber-500'
                            : insight.severity === 'warning'
                            ? 'bg-blue-500/10 text-blue-500'
                            : 'bg-primary/10 text-primary'
                        }`}
                      >
                        {insight.severity.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground mb-2">{insight.description}</p>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1 text-xs text-muted-foreground">
                        <Clock className="w-3 h-3" />
                        <span>{insight.time}</span>
                      </div>
                      <span className="text-xs text-primary/70">{insight.source}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
