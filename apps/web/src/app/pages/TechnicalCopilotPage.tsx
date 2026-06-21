import { Blocks, Bot, ShieldCheck, Sparkles } from 'lucide-react';
import { ChatHistory } from '../components/ChatHistory';
import { TechnicalCopilot } from '../components/TechnicalCopilot';
import { technicalCopilotKpis } from '../data/technicalCopilotMock';
import { useTechnicalCopilotChat } from '../hooks/useTechnicalCopilotChat';

const kpiIcons = {
  docs: Blocks,
  guides: ShieldCheck,
  tickets: Bot,
  latency: Sparkles,
};

export function TechnicalCopilotPage() {
  const copilot = useTechnicalCopilotChat();

  return (
    <div className="flex h-full min-h-0 bg-background">
      <ChatHistory
        conversations={copilot.filteredConversations}
        activeConversationId={copilot.activeConversationId}
        searchQuery={copilot.searchQuery}
        onSearchChange={copilot.setSearchQuery}
        onNewConversation={copilot.startNewConversation}
        onSelectConversation={copilot.selectConversation}
        onDeleteConversation={copilot.deleteConversation}
      />

      <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
        <div className="border-b border-border bg-card/50 backdrop-blur-sm">
          <div className="p-6 md:p-8">
            <div className="grid gap-6 xl:grid-cols-[minmax(0,1.4fr)_minmax(360px,0.9fr)]">
              <div className="rounded-[32px] border border-border bg-[linear-gradient(135deg,rgba(14,165,233,0.15),rgba(14,165,233,0.04)_42%,rgba(19,20,26,0.98)_100%)] p-6">
                <div className="mb-4 flex flex-wrap items-center gap-2">
                  <span className="rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-primary">
                    Copiloto tecnico
                  </span>
                  <span className="rounded-full border border-border bg-background/60 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                    Integracao inicial
                  </span>
                </div>

                <h2 className="max-w-3xl text-3xl font-bold leading-tight text-foreground md:text-4xl">
                  Interface principal conectada para request real sem desmontar a arquitetura
                  visual.
                </h2>
                <p className="mt-4 max-w-2xl text-sm leading-6 text-muted-foreground md:text-base">
                  Esta entrega preserva o layout existente, introduz uma camada HTTP configuravel e
                  deixa o fluxo principal do copiloto pronto para conversar com a nova API Python.
                </p>
              </div>

              <div className="rounded-[32px] border border-border bg-card p-6">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  Pronto para a proxima fase
                </p>
                <div className="mt-4 space-y-4">
                  <div className="rounded-2xl border border-border bg-muted/20 p-4">
                    <p className="text-sm font-medium text-foreground">Fronteira de integracao</p>
                    <p className="mt-1 text-sm leading-6 text-muted-foreground">
                      A UI agora depende de um cliente HTTP e de adapters de resposta, sem espalhar
                      dados mockados pelo fluxo principal do chat.
                    </p>
                  </div>
                  <div className="rounded-2xl border border-border bg-muted/20 p-4">
                    <p className="text-sm font-medium text-foreground">Troca futura simplificada</p>
                    <p className="mt-1 text-sm leading-6 text-muted-foreground">
                      Quando a API estiver disponivel neste monorepo, o acerto principal sera o
                      contrato das rotas, nao a reconstrucao da experiencia de chat.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain">
          <div className="space-y-6 p-6 md:p-8">
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              {technicalCopilotKpis.map((kpi) => {
                const Icon = kpiIcons[kpi.id as keyof typeof kpiIcons];

                return (
                  <div key={kpi.id} className="rounded-3xl border border-border bg-card p-5">
                    <div className="mb-4 flex items-start justify-between gap-3">
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                          {kpi.label}
                        </p>
                        <p className="mt-3 text-3xl font-bold text-primary">{kpi.value}</p>
                      </div>
                      <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-primary/10">
                        <Icon className="h-4 w-4 text-primary" />
                      </div>
                    </div>
                    <p className="text-sm text-muted-foreground">{kpi.caption}</p>
                  </div>
                );
              })}
            </div>

            <div className="h-[calc(100vh-24rem)] min-h-[42rem]">
              <TechnicalCopilot
                conversationId={copilot.activeConversationId}
                editorResetKey={copilot.editorResetKey}
                messages={copilot.messages}
                error={copilot.error}
                isSubmitting={copilot.isSubmitting}
                apiStatus={copilot.apiStatus}
                onClearError={copilot.clearError}
                onSubmit={copilot.submitMessage}
                onRetry={copilot.retryMessage}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
