import { useState } from 'react';
import { Download, Calendar, Filter, Activity, Shield, Lock, TrendingUp, Award, BarChart3, X, RefreshCw } from 'lucide-react';
import { useGovernance } from '../hooks/useGovernance';
import type { GovernanceReport } from '../types/governance';

function StateBadge({ state }: { state: string }) {
  const base = 'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium';
  if (state === 'Accepted') return <span className={`${base} bg-emerald-500/10 text-emerald-400`}>Aceito</span>;
  if (state === 'Denied') return <span className={`${base} bg-destructive/10 text-destructive`}>Negado</span>;
  return <span className={`${base} bg-amber-500/10 text-amber-400`}>Falhou</span>;
}

function SkeletonCard() {
  return (
    <div className="bg-card border border-border rounded-lg p-4 animate-pulse">
      <div className="h-3 bg-muted rounded w-24 mb-3" />
      <div className="h-8 bg-muted rounded w-16 mb-1" />
      <div className="h-3 bg-muted rounded w-20" />
    </div>
  );
}

function ReportModal({ markdown, onClose }: { markdown: string; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-card border border-border rounded-xl w-full max-w-3xl max-h-[80vh] flex flex-col shadow-2xl">
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <h3 className="text-sm font-semibold text-foreground">Relatório Executivo de Governança</h3>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-6">
          <pre className="text-xs text-muted-foreground whitespace-pre-wrap font-mono leading-relaxed">{markdown}</pre>
        </div>
        <div className="px-6 py-4 border-t border-border flex justify-end">
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
            className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary/90 text-primary-foreground rounded-lg transition-colors text-sm"
          >
            <Download className="w-4 h-4" />
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

  const handleExport = async () => {
    setReportLoading(true);
    const result = await fetchReport();
    setReportLoading(false);
    if (result) setReport(result);
  };

  const analysis = preview?.analysis;

  return (
    <div>
      {report && <ReportModal markdown={report.report_markdown} onClose={() => setReport(null)} />}

      <div className="border-b border-border bg-card/50 backdrop-blur-sm mb-6">
        <div className="p-8 pb-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-foreground mb-2">Governança IA</h2>
              <p className="text-muted-foreground">
                Análise de correlação e eventos de segurança em tempo real
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={refresh}
                className="flex items-center gap-2 px-4 py-2 bg-muted hover:bg-muted/70 rounded-lg transition-colors"
              >
                <RefreshCw className="w-4 h-4 text-foreground" />
                <span className="text-sm text-foreground">Atualizar</span>
              </button>
              <button className="flex items-center gap-2 px-4 py-2 bg-muted hover:bg-muted/70 rounded-lg transition-colors">
                <Filter className="w-4 h-4 text-foreground" />
                <span className="text-sm text-foreground">Filtrar</span>
              </button>
              <button
                onClick={handleExport}
                disabled={reportLoading}
                className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary/90 text-primary-foreground rounded-lg transition-colors disabled:opacity-60"
              >
                <Calendar className="w-4 h-4" />
                <span className="text-sm">{reportLoading ? 'Gerando...' : 'Exportar'}</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="px-8 space-y-6">
        {error && (
          <div className="bg-destructive/10 border border-destructive/30 text-destructive rounded-lg px-4 py-3 text-sm">
            {error}
          </div>
        )}

        <div className="grid grid-cols-6 gap-4">
          {loading ? (
            Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)
          ) : (
            <>
              <div className="bg-card border border-border rounded-lg p-4">
                <div className="flex items-start justify-between mb-3">
                  <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Total de Eventos</h3>
                  <Activity className="w-4 h-4 text-primary" />
                </div>
                <p className="text-3xl font-bold text-primary mb-1">{analysis?.total_log_entries ?? 0}</p>
                <p className="text-xs text-muted-foreground">eventos processados</p>
              </div>

              <div className="bg-card border border-border rounded-lg p-4">
                <div className="flex items-start justify-between mb-3">
                  <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Autenticação</h3>
                  <Shield className="w-4 h-4 text-primary" />
                </div>
                <p className="text-3xl font-bold text-primary mb-1">{analysis?.total_authentications ?? 0}</p>
                <p className="text-xs text-muted-foreground">tentativas registradas</p>
              </div>

              <div className="bg-card border border-border rounded-lg p-4">
                <div className="flex items-start justify-between mb-3">
                  <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Acesso Negado</h3>
                  <Lock className="w-4 h-4 text-primary" />
                </div>
                <p className="text-3xl font-bold text-primary mb-1">{analysis?.denied_access_count ?? 0}</p>
                <p className="text-xs text-muted-foreground">bloqueios efetuados</p>
              </div>

              <div className="bg-card border border-border rounded-lg p-4">
                <div className="flex items-start justify-between mb-3">
                  <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Taxa de Sucesso</h3>
                  <TrendingUp className="w-4 h-4 text-primary" />
                </div>
                <p className="text-3xl font-bold text-primary mb-1">
                  {analysis ? `${analysis.success_rate.toFixed(1)}%` : '—'}
                </p>
                <p className="text-xs text-muted-foreground">índice de precisão</p>
              </div>

              <div className="bg-card border border-border rounded-lg p-4">
                <div className="flex items-start justify-between mb-3">
                  <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Score de Risco</h3>
                  <Award className="w-4 h-4 text-primary" />
                </div>
                <p className={`text-3xl font-bold mb-1 ${(analysis?.risk_score ?? 0) >= 50 ? 'text-destructive' : 'text-primary'}`}>
                  {analysis?.risk_score ?? 0}
                </p>
                <p className="text-xs text-muted-foreground">pontuação (0–100)</p>
              </div>

              <div className="bg-card border border-border rounded-lg p-4">
                <div className="flex items-start justify-between mb-3">
                  <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Usuários Únicos</h3>
                  <BarChart3 className="w-4 h-4 text-primary" />
                </div>
                <p className="text-3xl font-bold text-primary mb-1">{analysis?.unique_users_count ?? 0}</p>
                <p className="text-xs text-muted-foreground">identidades ativas</p>
              </div>
            </>
          )}
        </div>

        <div className="bg-card border border-border rounded-xl overflow-hidden">
          <div className="p-6 border-b border-border">
            <h3 className="text-sm font-semibold text-foreground">Eventos de Segurança</h3>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border bg-muted/20">
                  <th className="text-left text-xs font-medium text-muted-foreground px-6 py-3">Data/Hora</th>
                  <th className="text-left text-xs font-medium text-muted-foreground px-6 py-3">Usuário (pseudônimo)</th>
                  <th className="text-left text-xs font-medium text-muted-foreground px-6 py-3">Aplicação</th>
                  <th className="text-left text-xs font-medium text-muted-foreground px-6 py-3">Estado</th>
                  <th className="text-left text-xs font-medium text-muted-foreground px-6 py-3">Sinal de Risco</th>
                  <th className="text-left text-xs font-medium text-muted-foreground px-6 py-3">IP</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  Array.from({ length: 8 }).map((_, i) => (
                    <tr key={i} className="border-b border-border">
                      {Array.from({ length: 6 }).map((_, j) => (
                        <td key={j} className="px-6 py-3">
                          <div className="h-4 bg-muted rounded animate-pulse w-24" />
                        </td>
                      ))}
                    </tr>
                  ))
                ) : (
                  (preview?.preview_rows ?? []).map((row, index) => (
                    <tr
                      key={index}
                      className="border-b border-border hover:bg-muted/10 transition-colors"
                    >
                      <td className="text-xs text-muted-foreground px-6 py-3 font-mono">
                        {new Date(row.timestamp).toLocaleString('pt-BR')}
                      </td>
                      <td className="text-xs text-foreground px-6 py-3 font-mono">{row.principalId}</td>
                      <td className="text-sm text-foreground px-6 py-3">{row.applicationName}</td>
                      <td className="px-6 py-3">
                        <StateBadge state={row.accessState} />
                      </td>
                      <td className="text-xs text-muted-foreground px-6 py-3">
                        {row.riskSignal === 'OK' ? (
                          <span className="text-emerald-400">OK</span>
                        ) : (
                          <span className="text-amber-400">{row.riskSignal}</span>
                        )}
                      </td>
                      <td className="text-xs text-muted-foreground px-6 py-3 font-mono">{row.source_ip}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
