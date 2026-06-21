import { Bell, Clock, Server, Shield } from 'lucide-react';

export function Header() {
  return (
    <div className="border-b border-border bg-card/50 backdrop-blur-sm">
      <div className="p-8 pb-6">
        <div className="mb-4 flex items-start justify-between gap-4">
          <div>
            <h1 className="mb-2 text-3xl font-bold text-foreground">
              Centro de Operações de Segurança com IA
            </h1>
            <p className="text-muted-foreground">
              Plataforma unificada de IA para operações e governança em cibersegurança
            </p>
          </div>
          <button className="flex items-center gap-2 rounded-lg bg-muted px-4 py-2 transition-colors hover:bg-muted/70">
            <Bell className="h-4 w-4 text-primary" />
            <span className="text-sm text-foreground">3 alertas</span>
          </button>
        </div>

        <div className="flex flex-wrap items-center gap-4 text-xs">
          <div className="flex items-center gap-2 rounded-md border border-primary/20 bg-primary/10 px-3 py-1.5">
            <div className="h-2 w-2 rounded-full bg-primary" />
            <span className="font-medium text-primary">Camada de IA conectável</span>
          </div>
          <div className="flex items-center gap-2 text-muted-foreground">
            <Shield className="h-3.5 w-3.5" />
            <span>Mascaramento de dados ativo</span>
          </div>
          <div className="flex items-center gap-2 text-muted-foreground">
            <Clock className="h-3.5 w-3.5" />
            <span>Processamento assíncrono em lote</span>
          </div>
          <div className="flex items-center gap-2 text-muted-foreground">
            <Server className="h-3.5 w-3.5" />
            <span>Infra preparada para integração futura</span>
          </div>
        </div>
      </div>
    </div>
  );
}
