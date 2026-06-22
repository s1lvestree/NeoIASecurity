import { MessageSquare, PanelLeftClose, PanelLeftOpen, Plus, Search, Trash2 } from 'lucide-react';
import type { ChatConversation } from '../types/chat';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from './ui/alert-dialog';

interface ChatHistoryProps {
  conversations: ChatConversation[];
  activeConversationId: string | null;
  searchQuery: string;
  onSearchChange: (value: string) => void;
  onNewConversation: () => void;
  onSelectConversation: (conversationId: string) => void;
  onDeleteConversation: (conversationId: string) => void;
  isCollapsed: boolean;
  onToggle: () => void;
}

function getDateLabel(value: string) {
  const date = new Date(value);
  const today = new Date();
  const todayStart = new Date(today.getFullYear(), today.getMonth(), today.getDate()).getTime();
  const dateStart = new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
  const days = Math.round((todayStart - dateStart) / 86_400_000);

  if (days === 0) return 'Hoje';
  if (days === 1) return 'Ontem';
  if (days > 1 && days < 7) return `${days} dias atras`;
  return new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: 'short' }).format(date);
}

function getTimeLabel(value: string) {
  return new Intl.DateTimeFormat('pt-BR', { hour: '2-digit', minute: '2-digit' }).format(
    new Date(value),
  );
}

export function ChatHistory({
  conversations,
  activeConversationId,
  searchQuery,
  onSearchChange,
  onNewConversation,
  onSelectConversation,
  onDeleteConversation,
  isCollapsed,
  onToggle,
}: ChatHistoryProps) {
  const groups = conversations.reduce<Record<string, ChatConversation[]>>((result, conversation) => {
    const label = getDateLabel(conversation.updatedAt);
    result[label] ??= [];
    result[label].push(conversation);
    return result;
  }, {});

  if (isCollapsed) {
    return (
      <aside className="hidden h-full w-14 flex-shrink-0 flex-col items-center border-r border-border bg-sidebar py-3 md:flex">
        <button
          type="button"
          onClick={onToggle}
          title="Expandir histórico"
          className="flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-sidebar-accent hover:text-sidebar-foreground"
        >
          <PanelLeftOpen className="h-5 w-5" />
        </button>
        <button
          type="button"
          onClick={onNewConversation}
          title="Nova conversa"
          className="mt-1 flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-sidebar-accent hover:text-sidebar-foreground"
        >
          <Plus className="h-5 w-5" />
        </button>
        <button
          type="button"
          title="Histórico de conversas"
          onClick={onToggle}
          className="mt-1 flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-sidebar-accent hover:text-sidebar-foreground"
        >
          <MessageSquare className="h-5 w-5" />
        </button>
      </aside>
    );
  }

  return (
    <aside className="hidden h-full w-72 flex-shrink-0 flex-col border-r border-border bg-sidebar md:flex">
      <div className="flex items-center gap-2 border-b border-border p-3">
        <button
          type="button"
          onClick={onToggle}
          title="Recolher histórico"
          className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-sidebar-accent hover:text-sidebar-foreground"
        >
          <PanelLeftClose className="h-5 w-5" />
        </button>
        <span className="text-sm font-medium text-sidebar-foreground">Conversas</span>
      </div>

      <div className="border-b border-border p-3">
        <button
          type="button"
          onClick={onNewConversation}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-primary-foreground transition-colors hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" />
          <span className="text-sm font-medium">Nova conversa</span>
        </button>
      </div>

      <div className="border-b border-border p-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="search"
            value={searchQuery}
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder="Buscar conversas"
            aria-label="Buscar conversas"
            className="w-full rounded-xl border border-border bg-muted/40 py-2 pl-9 pr-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain py-2">
        {conversations.length === 0 ? (
          <div className="px-5 py-8 text-center">
            <MessageSquare className="mx-auto h-5 w-5 text-muted-foreground" />
            <p className="mt-3 text-sm font-medium text-sidebar-foreground">
              {searchQuery ? 'Nenhuma conversa encontrada' : 'Nenhuma conversa salva'}
            </p>
            <p className="mt-1 text-xs leading-5 text-muted-foreground">
              {searchQuery
                ? 'Tente buscar por outro termo.'
                : 'Sua primeira conversa aparecera aqui depois do envio.'}
            </p>
          </div>
        ) : (
          Object.entries(groups).map(([date, dateConversations]) => (
            <div key={date} className="mb-4">
              <h3 className="px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                {date}
              </h3>
              <div className="space-y-1 px-2">
                {dateConversations.map((conversation) => {
                  const isActive = conversation.id === activeConversationId;
                  return (
                    <div
                      key={conversation.id}
                      className={`group flex items-start rounded-2xl border transition-colors ${
                        isActive
                          ? 'border-primary/20 bg-primary/10'
                          : 'border-transparent hover:border-border hover:bg-muted/40'
                      }`}
                    >
                      <button
                        type="button"
                        onClick={() => onSelectConversation(conversation.id)}
                        className="min-w-0 flex-1 px-3 py-3 text-left"
                      >
                        <div className="flex items-start gap-3">
                          <MessageSquare
                            className={`mt-0.5 h-4 w-4 flex-shrink-0 ${isActive ? 'text-primary' : 'text-muted-foreground'}`}
                          />
                          <div className="min-w-0 flex-1">
                            <div className="flex items-start justify-between gap-2">
                              <p className={`truncate text-sm font-medium ${isActive ? 'text-primary' : 'text-foreground'}`}>
                                {conversation.title}
                              </p>
                              <span className="text-[11px] text-muted-foreground">
                                {getTimeLabel(conversation.updatedAt)}
                              </span>
                            </div>
                            <p className="mt-1 line-clamp-2 text-xs leading-5 text-muted-foreground">
                              {conversation.preview}
                            </p>
                          </div>
                        </div>
                      </button>

                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <button
                            type="button"
                            aria-label={`Excluir ${conversation.title}`}
                            className="mr-2 mt-3 rounded-lg p-1.5 text-muted-foreground opacity-0 transition hover:bg-destructive/10 hover:text-destructive group-hover:opacity-100 focus:opacity-100"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>Excluir conversa?</AlertDialogTitle>
                            <AlertDialogDescription>
                              Esta acao remove permanentemente "{conversation.title}" deste navegador.
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>Cancelar</AlertDialogCancel>
                            <AlertDialogAction
                              onClick={() => onDeleteConversation(conversation.id)}
                              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                            >
                              Excluir
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    </div>
                  );
                })}
              </div>
            </div>
          ))
        )}
      </div>

      <div className="border-t border-border p-3">
        <div className="rounded-2xl border border-border bg-muted/20 p-3">
          <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Armazenamento</p>
          <p className="mt-2 text-sm font-medium text-sidebar-foreground">Historico local</p>
          <p className="mt-1 text-xs leading-5 text-muted-foreground">
            As conversas ficam salvas neste navegador.
          </p>
        </div>
      </div>
    </aside>
  );
}
