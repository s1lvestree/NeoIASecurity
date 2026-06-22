import { type ChangeEvent, type KeyboardEvent, useEffect, useRef, useState } from 'react';
import {
  AlertCircle,
  ArrowUp,
  CheckCircle2,
  Database,
  FileText,
  LoaderCircle,
  Lock,
  RefreshCw,
  Shield,
  Sparkles,
  WifiOff,
} from 'lucide-react';
import { quickActions, suggestedPrompts } from '../data/technicalCopilotMock';
import type { ApiHealthStatus, ChatMessage } from '../types/chat';

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
  onSubmit: (content: string) => Promise<'sent' | 'failed' | 'ignored'>;
  onRetry: (messageId: string) => Promise<'sent' | 'failed' | 'ignored'>;
}

function formatTime(value: string) {
  return new Intl.DateTimeFormat('pt-BR', { hour: '2-digit', minute: '2-digit' }).format(
    new Date(value),
  );
}

const apiStatusContent = {
  checking: { label: 'Verificando API', color: 'text-amber-500', Icon: LoaderCircle },
  online: { label: 'API conectada', color: 'text-emerald-400', Icon: CheckCircle2 },
  offline: { label: 'API indisponivel', color: 'text-red-500', Icon: WifiOff },
};

export function TechnicalCopilot({
  conversationId,
  editorResetKey,
  messages,
  error,
  isSubmitting,
  apiStatus,
  onClearError,
  onSubmit,
  onRetry,
}: TechnicalCopilotProps) {
  const [draft, setDraft] = useState('');
  const editorRef = useRef<HTMLTextAreaElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const status = apiStatusContent[apiStatus];
  const StatusIcon = status.Icon;

  useEffect(() => {
    setDraft('');
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

  const handleChange = (event: ChangeEvent<HTMLTextAreaElement>) => {
    if (error) onClearError();
    setDraft(event.target.value);
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      void handleSubmit();
    }
  };

  const isWelcome = messages.length === 0 && !error;

  if (isWelcome) {
    return (
      <div className="relative flex h-full flex-col items-center justify-center overflow-y-auto px-6 py-10">
        <div className={`absolute right-4 top-4 flex items-center gap-1.5 rounded-full border border-border bg-background/70 px-3 py-1.5 text-xs font-medium ${status.color}`}>
          <StatusIcon className={`h-3 w-3 ${apiStatus === 'checking' ? 'animate-spin' : ''}`} />
          {status.label}
        </div>

        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-primary/10">
            <Sparkles className="h-5 w-5 text-primary" />
          </div>
          <h1 className="text-2xl font-semibold text-foreground">O que posso te ajudar?</h1>
        </div>

        <form
          className="mt-6 w-full max-w-2xl"
          onSubmit={(event) => {
            event.preventDefault();
            void handleSubmit();
          }}
        >
          <div className="rounded-3xl border border-border bg-card p-4 shadow-md">
            <textarea
              ref={editorRef}
              value={draft}
              onChange={handleChange}
              onKeyDown={handleKeyDown}
              rows={3}
              placeholder="Pergunte sobre STA, DLP, SIEM, IAM/PAM ou troubleshooting."
              aria-label="Mensagem para o Copiloto"
              className="w-full resize-none bg-transparent text-sm leading-6 text-foreground outline-none placeholder:text-muted-foreground"
            />
            <div className="mt-3 flex items-center justify-between gap-3">
              <div className="flex flex-wrap gap-2">
                {quickActions.map((action) => {
                  const Icon = quickActionIcons[action.id as keyof typeof quickActionIcons];
                  return (
                    <button
                      key={action.id}
                      type="button"
                      onClick={() => preparePrompt(action.prompt)}
                      className="flex items-center gap-1.5 rounded-full border border-border bg-muted/40 px-3 py-1.5 text-xs transition-colors hover:bg-muted/70"
                    >
                      <Icon className={`h-3.5 w-3.5 ${action.accentClassName}`} />
                      <span className="text-foreground/90">{action.label}</span>
                    </button>
                  );
                })}
              </div>
              <button
                type="submit"
                aria-label="Enviar mensagem"
                disabled={isSubmitting || !draft.trim()}
                className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-foreground text-background disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isSubmitting ? (
                  <LoaderCircle className="h-4 w-4 animate-spin" />
                ) : (
                  <ArrowUp className="h-4 w-4" />
                )}
              </button>
            </div>
          </div>
        </form>

        <div className="mt-4 grid w-full max-w-2xl grid-cols-1 gap-3 md:grid-cols-3">
          {suggestedPrompts.map((prompt) => (
            <button
              key={prompt.id}
              type="button"
              onClick={() => preparePrompt(`${prompt.title}: ${prompt.description}`)}
              className="rounded-2xl border border-border bg-card/60 p-4 text-left transition-colors hover:border-primary/30 hover:bg-card/80"
            >
              <p className="text-sm font-medium text-foreground">{prompt.title}</p>
              <p className="mt-1 text-xs leading-5 text-muted-foreground">{prompt.description}</p>
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="min-h-0 flex-1 space-y-4 overflow-y-auto overscroll-contain bg-background p-6">
        {messages.map((message) => (
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

              <div className="mt-3 flex items-center justify-between gap-3 text-xs text-muted-foreground">
                <div className="flex items-center gap-2">
                  <span>{formatTime(message.createdAt)}</span>
                  {message.mode && (
                    <span className="rounded-full border border-border px-2 py-0.5 uppercase tracking-wide">
                      {message.mode}
                    </span>
                  )}
                  {message.deliveryStatus === 'pending' && (
                    <span className="flex items-center gap-1 text-amber-500">
                      <LoaderCircle className="h-3 w-3 animate-spin" /> Enviando
                    </span>
                  )}
                </div>
                {message.deliveryStatus === 'failed' && (
                  <button
                    type="button"
                    onClick={() => void onRetry(message.id)}
                    disabled={isSubmitting}
                    className="flex items-center gap-1.5 rounded-lg border border-red-800 px-2 py-1 text-red-400 hover:bg-red-950/60 disabled:opacity-50"
                  >
                    <RefreshCw className="h-3 w-3" /> Tentar novamente
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}

        {error && (
          <div className="rounded-3xl border border-red-800 bg-red-950/60 p-5">
            <div className="flex items-start gap-3">
              <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-red-400" />
              <div>
                <p className="text-sm font-medium text-red-400">Nao foi possivel concluir a acao</p>
                <p className="mt-1 text-sm leading-6 text-red-400/80">{error}</p>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="shrink-0 border-t border-border bg-background p-4">
        <form
          className="mx-auto max-w-2xl"
          onSubmit={(event) => {
            event.preventDefault();
            void handleSubmit();
          }}
        >
          <div className="rounded-3xl border border-border bg-card p-4 shadow-md">
            <textarea
              ref={editorRef}
              value={draft}
              onChange={handleChange}
              onKeyDown={handleKeyDown}
              rows={2}
              placeholder="Pergunte sobre STA, DLP, SIEM, IAM/PAM ou troubleshooting."
              aria-label="Mensagem para o Copiloto"
              className="w-full resize-none bg-transparent text-sm leading-6 text-foreground outline-none placeholder:text-muted-foreground"
            />
            <div className="mt-3 flex items-center justify-between gap-3">
              <div className="flex flex-wrap gap-2">
                {quickActions.map((action) => {
                  const Icon = quickActionIcons[action.id as keyof typeof quickActionIcons];
                  return (
                    <button
                      key={action.id}
                      type="button"
                      onClick={() => preparePrompt(action.prompt)}
                      className="flex items-center gap-1.5 rounded-full border border-border bg-muted/40 px-3 py-1.5 text-xs transition-colors hover:bg-muted/70"
                    >
                      <Icon className={`h-3.5 w-3.5 ${action.accentClassName}`} />
                      <span className="text-foreground/90">{action.label}</span>
                    </button>
                  );
                })}
              </div>
              <div className="flex flex-shrink-0 items-center gap-3">
                <div className={`flex items-center gap-1.5 text-xs font-medium ${status.color}`}>
                  <StatusIcon className={`h-3 w-3 ${apiStatus === 'checking' ? 'animate-spin' : ''}`} />
                  <span className="hidden sm:inline">{status.label}</span>
                </div>
                <button
                  type="submit"
                  aria-label="Enviar mensagem"
                  disabled={isSubmitting || !draft.trim()}
                  className="flex h-9 w-9 items-center justify-center rounded-full bg-foreground text-background disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {isSubmitting ? (
                    <LoaderCircle className="h-4 w-4 animate-spin" />
                  ) : (
                    <ArrowUp className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
