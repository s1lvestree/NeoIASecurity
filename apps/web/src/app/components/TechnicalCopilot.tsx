import { useEffect, useRef, useState } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  Database,
  FileText,
  ExternalLink,
  LoaderCircle,
  Lock,
  RefreshCw,
  Send,
  Shield,
  Sparkles,
  Trash2,
  WifiOff,
} from 'lucide-react';
import { quickActions, suggestedPrompts } from '../data/technicalCopilotMock';
import type { ApiHealthStatus, ChatMessage } from '../types/chat';
import { ticketService, type TicketResponse } from '../services/ticketService';
import { ApiError } from '../services/httpClient';

const quickActionIcons = {
  octadesk: FileText,
  sta: Shield,
  dlp: Database,
  iam: Lock,
};

interface TechnicalCopilotProps {
  conversationId: string | null;
  editorResetKey: number;
  messages: ChatMessage[];
  error: string | null;
  isSubmitting: boolean;
  apiStatus: ApiHealthStatus;
  onClearError: () => void;
  onClearConversation: () => void;
  onSubmit: (content: string) => Promise<'sent' | 'failed' | 'ignored'>;
  onRetry: (messageId: string) => Promise<'sent' | 'failed' | 'ignored'>;
}

function formatTime(value: string) {
  return new Intl.DateTimeFormat('pt-BR', { hour: '2-digit', minute: '2-digit' }).format(
    new Date(value),
  );
}

const apiStatusContent = {
  checking: { label: 'Verificando API', color: 'text-amber-300', Icon: LoaderCircle },
  online: { label: 'API conectada', color: 'text-emerald-400', Icon: CheckCircle2 },
  offline: { label: 'API indisponivel', color: 'text-red-300', Icon: WifiOff },
};

interface TicketError {
  message: string;
  diagnostic?: string;
}

function ticketDiagnostic(error: unknown): string | undefined {
  if (!(error instanceof ApiError) || !error.details || typeof error.details !== 'object') {
    return undefined;
  }
  const responseBody = error.details as Record<string, unknown>;
  const detail = responseBody.detail;
  if (typeof detail === 'string') return detail;
  if (detail && typeof detail === 'object') {
    const nestedDetail = (detail as Record<string, unknown>).detail;
    if (typeof nestedDetail === 'string') return nestedDetail;
    const structured = detail as Record<string, unknown>;
    const parts = [structured.message, structured.zammad_error, structured.hint]
      .filter((value): value is string => typeof value === 'string' && value.length > 0);
    if (parts.length) return parts.join(' ');
  }
  return undefined;
}

export function TechnicalCopilot({
  conversationId,
  editorResetKey,
  messages,
  error,
  isSubmitting,
  apiStatus,
  onClearError,
  onClearConversation,
  onSubmit,
  onRetry,
}: TechnicalCopilotProps) {
  const [draft, setDraft] = useState('');
  const [ticketLoadingId, setTicketLoadingId] = useState<string | null>(null);
  const [ticketResults, setTicketResults] = useState<Record<string, TicketResponse>>({});
  const [ticketErrors, setTicketErrors] = useState<Record<string, TicketError>>({});
  const editorRef = useRef<HTMLTextAreaElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const status = apiStatusContent[apiStatus];
  const StatusIcon = status.Icon;

  useEffect(() => {
    setDraft('');
    setTicketLoadingId(null);
    setTicketResults({});
    setTicketErrors({});
    editorRef.current?.focus();
  }, [conversationId, editorResetKey]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [isSubmitting, messages]);

  const preparePrompt = (prompt: string) => {
    onClearError();
    setDraft(prompt);
  };

  const handleSubmit = async () => {
    const result = await onSubmit(draft);
    if (result !== 'ignored') setDraft('');
  };

  const handleCreateTicket = async (message: ChatMessage, messageIndex: number) => {
    const question = [...messages.slice(0, messageIndex)]
      .reverse()
      .find(({ role, deliveryStatus }) => role === 'user' && deliveryStatus === 'sent')?.content;
    if (!question || ticketLoadingId) return;

    setTicketLoadingId(message.id);
    setTicketErrors((current) => {
      const updated = { ...current };
      delete updated[message.id];
      return updated;
    });
    try {
      const result = await ticketService.createFromChat(question, message.content);
      setTicketResults((current) => ({ ...current, [message.id]: result }));
    } catch (error) {
      setTicketErrors((current) => ({
        ...current,
        [message.id]: {
          message:
            'Não foi possível criar o chamado no Zammad. Verifique a integração da plataforma de chamados.',
          diagnostic: ticketDiagnostic(error),
        },
      }));
    } finally {
      setTicketLoadingId(null);
    }
  };

  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden">
      <div className="shrink-0 border-b border-border bg-[linear-gradient(135deg,rgba(14,165,233,0.16),rgba(14,165,233,0.03)_45%,rgba(19,20,26,0.96)_100%)] px-6 py-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-primary/10">
              <Sparkles className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-foreground">Copiloto Tecnico</h3>
              <p className="text-sm text-muted-foreground">
                Troubleshooting e triagem com historico salvo neste navegador.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button type="button" onClick={onClearConversation} className="flex items-center gap-2 rounded-full border border-border bg-background/70 px-3 py-2 text-xs font-medium text-muted-foreground hover:text-foreground">
              <Trash2 className="h-3.5 w-3.5" /> Limpar conversa
            </button>
            <div className={`flex items-center gap-2 rounded-full border border-border bg-background/70 px-3 py-2 text-xs font-medium ${status.color}`}>
              <StatusIcon className={`h-3.5 w-3.5 ${apiStatus === 'checking' ? 'animate-spin' : ''}`} />
              {status.label}
            </div>
          </div>
        </div>
      </div>

      <div className="min-h-0 flex-1 space-y-4 overflow-y-auto overscroll-contain bg-[radial-gradient(circle_at_top,rgba(14,165,233,0.08),transparent_32%),linear-gradient(180deg,rgba(10,10,15,0.98),rgba(19,20,26,1))] p-6">
        {messages.length === 0 && (
          <div className="rounded-[28px] border border-border/80 bg-card/85 p-6">
            <div className="flex items-start gap-4">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary/10">
                <Sparkles className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-sm font-semibold text-foreground">Inicie uma nova analise</p>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
                  Envie uma pergunta sobre STA, DLP, SIEM ou IAM/PAM. A conversa sera salva
                  localmente depois do primeiro envio.
                </p>
              </div>
            </div>
          </div>
        )}

        {messages.map((message, messageIndex) => (
          <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[80%] rounded-3xl p-5 ${
                message.role === 'user'
                  ? 'border border-primary/30 bg-primary/10'
                  : 'border border-border/80 bg-card/90'
              } ${message.deliveryStatus === 'failed' ? 'border-red-500/40' : ''}`}
            >
              <p className="whitespace-pre-line text-sm leading-6 text-foreground">{message.content}</p>

              {message.references && message.references.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-2 border-t border-border/50 pt-4">
                  {message.references.map((reference) => (
                    <span key={reference} className="rounded-full border border-primary/20 bg-primary/10 px-2.5 py-1 text-[11px] font-medium text-primary">
                      {reference}
                    </span>
                  ))}
                </div>
              )}

              {message.role === 'assistant' &&
                messages.slice(0, messageIndex).some(({ role }) => role === 'user') && (
                  <div className="mt-4 border-t border-border/50 pt-4">
                    {!ticketResults[message.id] && (
                      <button
                        type="button"
                        onClick={() => void handleCreateTicket(message, messageIndex)}
                        disabled={ticketLoadingId !== null}
                        className="flex items-center gap-2 rounded-xl border border-primary/30 bg-primary/10 px-3 py-2 text-xs font-medium text-primary hover:bg-primary/15 disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        {ticketLoadingId === message.id && <LoaderCircle className="h-3.5 w-3.5 animate-spin" />}
                        Não resolveu - abrir chamado
                      </button>
                    )}
                    {ticketResults[message.id] && (
                      <div className="space-y-2 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs text-emerald-100">
                        <p className="font-medium">Chamado criado com sucesso no Zammad.</p>
                        <p>Número do chamado: {ticketResults[message.id].ticket_number ?? 'não informado'}</p>
                        <p>ID do chamado: {ticketResults[message.id].ticket_id ?? 'não informado'}</p>
                        {ticketResults[message.id].customer_email && (
                          <p>Cliente: {ticketResults[message.id].customer_email}</p>
                        )}
                        {ticketResults[message.id].created_customer && (
                          <p>Cliente criado automaticamente no Zammad.</p>
                        )}
                        {ticketResults[message.id].ticket_url && (
                          <a
                            href={ticketResults[message.id].ticket_url!}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-1 font-medium underline"
                          >
                            Abrir no Zammad <ExternalLink className="h-3 w-3" />
                          </a>
                        )}
                        {ticketResults[message.id].email_notification?.warning && (
                          <p className="text-amber-200">O chamado foi criado, mas uma notificação por e-mail falhou.</p>
                        )}
                      </div>
                    )}
                    {ticketErrors[message.id] && (
                      <div className="mt-2 rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-200">
                        <p>{ticketErrors[message.id].message}</p>
                        {ticketErrors[message.id].diagnostic && (
                          <details className="mt-2">
                            <summary className="cursor-pointer font-medium">Detalhes de diagnóstico</summary>
                            <p className="mt-1 text-red-100/80">
                              {ticketErrors[message.id].diagnostic}
                            </p>
                          </details>
                        )}
                      </div>
                    )}
                  </div>
                )}

              <div className="mt-3 flex items-center justify-between gap-3 text-xs text-muted-foreground">
                <div className="flex items-center gap-2">
                  <span>{formatTime(message.createdAt)}</span>
                  {message.mode === 'fallback' && (
                    <details className="relative">
                      <summary className="cursor-pointer list-none rounded-full border border-border px-2 py-0.5">Detalhes técnicos</summary>
                      <span className="absolute bottom-6 left-0 z-10 whitespace-nowrap rounded-lg border border-border bg-background px-3 py-2 shadow-lg">Resposta local</span>
                    </details>
                  )}
                  {message.mode === 'bedrock' && <span className="rounded-full border border-border px-2 py-0.5">Bedrock</span>}
                  {message.deliveryStatus === 'pending' && (
                    <span className="flex items-center gap-1 text-amber-300">
                      <LoaderCircle className="h-3 w-3 animate-spin" /> Enviando
                    </span>
                  )}
                </div>
                {message.deliveryStatus === 'failed' && (
                  <button
                    type="button"
                    onClick={() => void onRetry(message.id)}
                    disabled={isSubmitting}
                    className="flex items-center gap-1.5 rounded-lg border border-red-500/30 px-2 py-1 text-red-200 hover:bg-red-500/10 disabled:opacity-50"
                  >
                    <RefreshCw className="h-3 w-3" /> Tentar novamente
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}

        {error && (
          <div className="rounded-3xl border border-red-500/30 bg-red-500/10 p-5">
            <div className="flex items-start gap-3">
              <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-red-300" />
              <div>
                <p className="text-sm font-medium text-red-100">Nao foi possivel concluir a acao</p>
                <p className="mt-1 text-sm leading-6 text-red-100/80">{error}</p>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="shrink-0 border-t border-border bg-card/70 p-5 backdrop-blur-sm">
        <div className="mb-4 flex flex-wrap gap-2">
          {quickActions.map((action) => {
            const Icon = quickActionIcons[action.id as keyof typeof quickActionIcons];
            return (
              <button
                key={action.id}
                type="button"
                onClick={() => preparePrompt(action.prompt)}
                className="flex items-center gap-2 rounded-full border border-border bg-muted/40 px-3 py-2 text-xs transition-colors hover:bg-muted/70"
              >
                <Icon className={`h-4 w-4 ${action.accentClassName}`} />
                <span className="text-foreground/90">{action.label}</span>
              </button>
            );
          })}
        </div>

        <div className="mb-4 grid gap-3 md:grid-cols-3">
          {suggestedPrompts.map((prompt) => (
            <button
              key={prompt.id}
              type="button"
              onClick={() => preparePrompt(`${prompt.title}: ${prompt.description}`)}
              className="rounded-2xl border border-border bg-background/60 p-4 text-left transition-colors hover:border-primary/30 hover:bg-background/80"
            >
              <p className="text-sm font-medium text-foreground">{prompt.title}</p>
              <p className="mt-1 text-xs leading-5 text-muted-foreground">{prompt.description}</p>
            </button>
          ))}
        </div>

        <form
          className="flex gap-3"
          onSubmit={(event) => {
            event.preventDefault();
            void handleSubmit();
          }}
        >
          <div className="flex-1 rounded-2xl border border-border bg-background/65 px-4 py-3">
            <textarea
              ref={editorRef}
              value={draft}
              onChange={(event) => {
                if (error) onClearError();
                setDraft(event.target.value);
              }}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault();
                  void handleSubmit();
                }
              }}
              rows={3}
              placeholder="Pergunte sobre STA, DLP, SIEM, IAM/PAM ou troubleshooting."
              aria-label="Mensagem para o Copiloto"
              className="w-full resize-none bg-transparent text-sm leading-6 text-foreground outline-none placeholder:text-muted-foreground"
            />
          </div>
          <button
            type="submit"
            aria-label="Enviar mensagem"
            disabled={isSubmitting || !draft.trim()}
            className="flex items-center justify-center rounded-2xl bg-primary px-5 text-primary-foreground disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSubmitting ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </button>
        </form>
      </div>
    </div>
  );
}
