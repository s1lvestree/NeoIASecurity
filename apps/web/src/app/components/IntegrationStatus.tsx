import { CheckCircle2, AlertCircle } from 'lucide-react';

const integrations = [
  { name: 'STA Logs API', status: 'connected', endpoint: 'api.sta.local' },
  { name: 'Octadesk API', status: 'connected', endpoint: 'api.octadesk.com' },
  { name: 'DLP/Safetica', status: 'pending', endpoint: 'Aguardando configuração' },
  { name: 'Integração SIEM', status: 'pending', endpoint: 'Fase 2' },
];

export function IntegrationStatus() {
  return (
    <div className="bg-card border border-border rounded-xl p-6">
      <h3 className="text-sm font-semibold text-foreground mb-4">Integrações do Sistema</h3>
      <div className="space-y-3">
        {integrations.map((integration) => (
          <div key={integration.name} className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {integration.status === 'connected' ? (
                <CheckCircle2 className="w-4 h-4 text-primary" />
              ) : (
                <AlertCircle className="w-4 h-4 text-muted-foreground" />
              )}
              <div>
                <p className="text-sm text-foreground">{integration.name}</p>
                <p className="text-xs text-muted-foreground">{integration.endpoint}</p>
              </div>
            </div>
            <span
              className={`text-xs px-2 py-1 rounded-md ${
                integration.status === 'connected'
                  ? 'bg-primary/10 text-primary'
                  : 'bg-muted text-muted-foreground'
              }`}
            >
              {integration.status === 'connected' ? 'Conectado' : 'Pendente'}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
