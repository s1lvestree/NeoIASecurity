import { MetricCard } from '../components/MetricCard';
import { IntegrationStatus } from '../components/IntegrationStatus';
import { Activity, FileText, Headphones, Shield, TrendingUp, Users, AlertTriangle } from 'lucide-react';

export function Dashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-foreground mb-2">Visão Geral</h2>
        <p className="text-muted-foreground">
          Status em tempo real das operações de segurança e plataforma de IA
        </p>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <MetricCard
          icon={Activity}
          label="Eventos Processados"
          value="1.247"
          change="+12,5%"
          trend="up"
        />
        <MetricCard
          icon={FileText}
          label="Relatórios Gerados"
          value="38"
          change="+8,3%"
          trend="up"
        />
        <MetricCard
          icon={Headphones}
          label="Chamados Assistidos"
          value="142"
          change="-3,2%"
          trend="down"
        />
        <MetricCard
          icon={Shield}
          label="Score de Risco"
          value="75/100"
          change="+5,1%"
          trend="down"
        />
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-6">
          <div className="bg-card border border-border rounded-xl p-6">
            <h3 className="text-sm font-semibold text-foreground mb-4">Atividades Recentes</h3>
            <div className="space-y-4">
              <div className="flex items-start gap-4 pb-4 border-b border-border">
                <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Shield className="w-5 h-5 text-primary" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <h4 className="text-sm font-medium text-foreground">Análise de Logs STA Concluída</h4>
                    <span className="text-xs text-muted-foreground">5 min atrás</span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Processados 1.240 eventos de autenticação. 32 descobertas críticas identificadas.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4 pb-4 border-b border-border">
                <div className="w-10 h-10 bg-amber-500/10 rounded-lg flex items-center justify-center flex-shrink-0">
                  <AlertTriangle className="w-5 h-5 text-amber-500" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <h4 className="text-sm font-medium text-foreground">Alerta de Usuário de Alto Risco</h4>
                    <span className="text-xs text-muted-foreground">12 min atrás</span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    DLP/Safetica detectou 4 usuários com violações repetidas de política.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4 pb-4 border-b border-border">
                <div className="w-10 h-10 bg-blue-500/10 rounded-lg flex items-center justify-center flex-shrink-0">
                  <FileText className="w-5 h-5 text-blue-500" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <h4 className="text-sm font-medium text-foreground">Relatório Executivo Gerado</h4>
                    <span className="text-xs text-muted-foreground">1 hora atrás</span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Resumo semanal de segurança enviado para equipe de governança.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Headphones className="w-5 h-5 text-primary" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <h4 className="text-sm font-medium text-foreground">Chamado Criado via IA</h4>
                    <span className="text-xs text-muted-foreground">2 horas atrás</span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Chamado Octadesk #4829 criado após aprovação de revisão humana.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-card border border-border rounded-xl p-6">
            <h3 className="text-sm font-semibold text-foreground mb-4">Performance do Sistema</h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-4 bg-muted/20 rounded-lg">
                <div className="flex items-center justify-center gap-2 mb-2">
                  <TrendingUp className="w-4 h-4 text-primary" />
                  <span className="text-xs text-muted-foreground">Resposta Média</span>
                </div>
                <p className="text-xl font-bold text-foreground">2,3s</p>
              </div>
              <div className="text-center p-4 bg-muted/20 rounded-lg">
                <div className="flex items-center justify-center gap-2 mb-2">
                  <Activity className="w-4 h-4 text-primary" />
                  <span className="text-xs text-muted-foreground">Disponibilidade</span>
                </div>
                <p className="text-xl font-bold text-foreground">99,8%</p>
              </div>
              <div className="text-center p-4 bg-muted/20 rounded-lg">
                <div className="flex items-center justify-center gap-2 mb-2">
                  <Users className="w-4 h-4 text-primary" />
                  <span className="text-xs text-muted-foreground">Usuários Ativos</span>
                </div>
                <p className="text-xl font-bold text-foreground">23</p>
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <IntegrationStatus />
          <div className="bg-card border border-border rounded-xl p-6">
            <h3 className="text-sm font-semibold text-foreground mb-4">Fila de Processamento</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-muted/20 rounded-lg">
                <div>
                  <p className="text-sm text-foreground">Análise de Logs STA</p>
                  <p className="text-xs text-muted-foreground">Agendado: 23:00</p>
                </div>
                <span className="text-xs text-primary">Na fila</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-muted/20 rounded-lg">
                <div>
                  <p className="text-sm text-foreground">Relatório Diário DLP</p>
                  <p className="text-xs text-muted-foreground">Agendado: 00:30</p>
                </div>
                <span className="text-xs text-primary">Na fila</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-primary/10 rounded-lg border border-primary/20">
                <div>
                  <p className="text-sm text-foreground">Resumo Executivo</p>
                  <p className="text-xs text-primary">Processando...</p>
                </div>
                <div className="w-2 h-2 bg-primary rounded-full animate-pulse" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
