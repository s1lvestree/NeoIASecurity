import { ArrowUpRight, ArrowDownRight, Download, Calendar, Filter, Activity, Shield, Lock, TrendingUp, Award, BarChart3 } from 'lucide-react';

const correlationData = {
  total: 686,
  autenticacao: 343,
  acesso: 343,
  percentual: 76.38,
  score: 17,
  ranking: 16,
};

const eventData = [
  {
    dataHora: '2024-06-17 14:24:07',
    usuario: 'José Silva',
    acao: 'ADT1 Permission',
    dispositivo: 'ZORK',
    horario: '15:43:13',
    ip: '192.168.1.1',
    direcao: 'up',
  },
  {
    dataHora: '2024-06-17 14:23:07',
    usuario: 'marcos.gomes',
    acao: 'Office 365',
    dispositivo: 'ZORK',
    horario: '14:31:17',
    ip: '10.0.0.25',
    direcao: 'down',
  },
  {
    dataHora: '2024-06-17 14:22:07',
    usuario: 'José Silva',
    acao: 'TeamViewer',
    dispositivo: '',
    horario: '14:30:14',
    ip: '172.16.0.5',
    direcao: 'up',
  },
  {
    dataHora: '2024-06-17 14:21:07',
    usuario: 'ana.costa',
    acao: 'ADT1 Permission',
    dispositivo: 'ZORK',
    horario: '15:43:13',
    ip: '192.168.1.50',
    direcao: 'down',
  },
  {
    dataHora: '2024-06-17 14:20:07',
    usuario: 'marcos.gomes',
    acao: 'Office 365',
    dispositivo: 'ZORK',
    horario: '14:31:17',
    ip: '10.0.0.30',
    direcao: 'up',
  },
  {
    dataHora: '2024-06-17 14:19:07',
    usuario: 'José Silva',
    acao: 'TeamViewer',
    dispositivo: '',
    horario: '16:21:18',
    ip: '172.16.0.10',
    direcao: 'down',
  },
  {
    dataHora: '2024-06-17 14:18:07',
    usuario: 'ana.costa',
    acao: 'ADT1 Permission',
    dispositivo: 'ZORK',
    horario: '15:43:13',
    ip: '192.168.1.75',
    direcao: 'up',
  },
  {
    dataHora: '2024-06-17 14:17:07',
    usuario: 'marcos.gomes',
    acao: 'Office 365',
    dispositivo: 'ZORK',
    horario: '14:31:17',
    ip: '10.0.0.45',
    direcao: 'down',
  },
  {
    dataHora: '2024-06-17 14:16:07',
    usuario: 'José Silva',
    acao: 'Office 365',
    dispositivo: 'ZORK',
    horario: '15:43:13',
    ip: '192.168.1.100',
    direcao: 'up',
  },
  {
    dataHora: '2024-06-17 14:15:07',
    usuario: 'ana.costa',
    acao: 'TeamViewer',
    dispositivo: '',
    horario: '16:21:18',
    ip: '172.16.0.15',
    direcao: 'down',
  },
];

export function GovernancePage() {
  return (
    <div>
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
              <button className="flex items-center gap-2 px-4 py-2 bg-muted hover:bg-muted/70 rounded-lg transition-colors">
                <Filter className="w-4 h-4 text-foreground" />
                <span className="text-sm text-foreground">Filtrar</span>
              </button>
              <button className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary/90 text-primary-foreground rounded-lg transition-colors">
                <Calendar className="w-4 h-4" />
                <span className="text-sm">Exportar</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="px-8 space-y-6">

      <div className="grid grid-cols-6 gap-4 mb-6">
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-start justify-between mb-3">
            <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Total de Eventos</h3>
            <Activity className="w-4 h-4 text-primary" />
          </div>
          <p className="text-3xl font-bold text-primary mb-1">{correlationData.total}</p>
          <p className="text-xs text-muted-foreground">eventos processados</p>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-start justify-between mb-3">
            <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Autenticação</h3>
            <Shield className="w-4 h-4 text-primary" />
          </div>
          <p className="text-3xl font-bold text-primary mb-1">{correlationData.autenticacao}</p>
          <p className="text-xs text-muted-foreground">tentativas registradas</p>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-start justify-between mb-3">
            <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Acesso Negado</h3>
            <Lock className="w-4 h-4 text-primary" />
          </div>
          <p className="text-3xl font-bold text-primary mb-1">{correlationData.acesso}</p>
          <p className="text-xs text-muted-foreground">bloqueios efetuados</p>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-start justify-between mb-3">
            <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Taxa Correlação</h3>
            <TrendingUp className="w-4 h-4 text-primary" />
          </div>
          <p className="text-3xl font-bold text-primary mb-1">{correlationData.percentual}%</p>
          <p className="text-xs text-muted-foreground">índice de precisão</p>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-start justify-between mb-3">
            <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Score</h3>
            <Award className="w-4 h-4 text-primary" />
          </div>
          <p className="text-3xl font-bold text-primary mb-1">{correlationData.score}</p>
          <p className="text-xs text-muted-foreground">pontuação atual</p>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-start justify-between mb-3">
            <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Ranking/Score</h3>
            <BarChart3 className="w-4 h-4 text-primary" />
          </div>
          <p className="text-3xl font-bold text-primary mb-1">{correlationData.ranking}</p>
          <p className="text-xs text-muted-foreground">posição relativa</p>
        </div>
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
                <th className="text-left text-xs font-medium text-muted-foreground px-6 py-3">Nome de usuário</th>
                <th className="text-left text-xs font-medium text-muted-foreground px-6 py-3">Ação</th>
                <th className="text-left text-xs font-medium text-muted-foreground px-6 py-3">Dispositivo</th>
                <th className="text-left text-xs font-medium text-muted-foreground px-6 py-3">Horário</th>
                <th className="text-left text-xs font-medium text-muted-foreground px-6 py-3">IP</th>
              </tr>
            </thead>
            <tbody>
              {eventData.map((event, index) => (
                <tr
                  key={index}
                  className="border-b border-border hover:bg-muted/10 transition-colors"
                >
                  <td className="text-sm text-foreground px-6 py-3">{event.dataHora}</td>
                  <td className="text-sm text-foreground px-6 py-3">{event.usuario}</td>
                  <td className="text-sm text-foreground px-6 py-3">{event.acao}</td>
                  <td className="text-sm text-muted-foreground px-6 py-3">{event.dispositivo || '-'}</td>
                  <td className="text-sm text-foreground px-6 py-3">{event.horario}</td>
                  <td className="text-sm px-6 py-3">
                    <div className="flex items-center gap-2">
                      <span className="text-foreground">{event.ip}</span>
                      {event.direcao === 'up' ? (
                        <ArrowUpRight className="w-4 h-4 text-primary" />
                      ) : (
                        <ArrowDownRight className="w-4 h-4 text-destructive" />
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      </div>
    </div>
  );
}
