import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { apiChatService, type ChatService } from '../services/chatService';
import {
  LocalStorageConversationRepository,
  type ConversationRepository,
} from '../services/conversationRepository';
import { apiHealthService, type HealthService } from '../services/healthService';
import type { ApiHealthStatus, ChatConversation, ChatMessage } from '../types/chat';

const API_ERROR_MESSAGE = 'Não foi possível obter resposta da API. Verifique se o backend está ativo e tente novamente.';
const INITIAL_GREETING: ChatMessage = {
  id: 'assistant-initial-greeting-v2',
  role: 'assistant',
  content: 'Olá! Sou o Copiloto Técnico da NeoIA Security. Como posso ajudar?',
  createdAt: new Date().toISOString(),
  deliveryStatus: 'sent',
};

interface CopilotDependencies {
  repository?: ConversationRepository;
  chatService?: ChatService;
  healthService?: HealthService;
}

function createId(prefix: string) {
  const suffix = globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  return `${prefix}-${suffix}`;
}

function truncate(value: string, maximumLength: number) {
  return value.length <= maximumLength ? value : `${value.slice(0, maximumLength - 1).trimEnd()}...`;
}

function sortByRecent(conversations: ChatConversation[]) {
  return [...conversations].sort((left, right) => right.updatedAt.localeCompare(left.updatedAt));
}

function normalizeSearch(value: string) {
  return value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLocaleLowerCase('pt-BR')
    .trim();
}

export function useTechnicalCopilotChat(dependencies: CopilotDependencies = {}) {
  const [services] = useState(() => ({
    repository: dependencies.repository ?? new LocalStorageConversationRepository(),
    chatService: dependencies.chatService ?? apiChatService,
    healthService: dependencies.healthService ?? apiHealthService,
  }));
  const [initialConversations] = useState(() => services.repository.list());
  const [conversations, setConversations] = useState<ChatConversation[]>(initialConversations);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(
    initialConversations[0]?.id ?? null,
  );
  const [searchQuery, setSearchQuery] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiStatus, setApiStatus] = useState<ApiHealthStatus>('checking');
  const [editorResetKey, setEditorResetKey] = useState(0);
  const requestGenerationRef = useRef(0);

  useEffect(() => {
    let isCurrent = true;

    void services.healthService.check().then(({ status }) => {
      if (isCurrent) {
        setApiStatus(status);
      }
    });

    return () => {
      isCurrent = false;
    };
  }, [services]);

  const activeConversation = useMemo(
    () => conversations.find(({ id }) => id === activeConversationId) ?? null,
    [activeConversationId, conversations],
  );

  const commitConversation = useCallback(
    (conversation: ChatConversation) => {
      setConversations((current) =>
        sortByRecent([conversation, ...current.filter(({ id }) => id !== conversation.id)]),
      );

      try {
        services.repository.save(conversation);
      } catch {
        setError('A conversa continua aberta, mas nao foi possivel salva-la neste navegador.');
      }
    },
    [services],
  );

  const requestAnswer = useCallback(
    async (conversation: ChatConversation, userMessage: ChatMessage) => {
      const requestGeneration = requestGenerationRef.current;
      setIsSubmitting(true);
      setError(null);

      try {
        const assistantMessage = await services.chatService.sendMessage({
          conversationId: conversation.id,
          content: userMessage.content,
        });
        if (requestGeneration !== requestGenerationRef.current) return 'ignored' as const;
        const updatedAt = new Date().toISOString();
        const completedConversation: ChatConversation = {
          ...conversation,
          preview: truncate(assistantMessage.content, 100),
          updatedAt,
          messages: [
            ...conversation.messages.map((message) =>
              message.id === userMessage.id
                ? { ...message, deliveryStatus: 'sent' as const }
                : message,
            ),
            { ...assistantMessage, deliveryStatus: 'sent' },
          ],
        };
        commitConversation(completedConversation);
        setApiStatus('online');
        return 'sent' as const;
      } catch (submissionError) {
        if (requestGeneration !== requestGenerationRef.current) return 'ignored' as const;
        console.error('Falha na consulta à API do copiloto:', submissionError instanceof Error ? submissionError.name : 'erro desconhecido');
        const updatedAt = new Date().toISOString();
        commitConversation({
          ...conversation,
          updatedAt,
          messages: conversation.messages.map((message) =>
            message.id === userMessage.id
              ? { ...message, deliveryStatus: 'failed' as const }
              : message,
          ),
        });
        setApiStatus('offline');
        setError(API_ERROR_MESSAGE);
        return 'failed' as const;
      } finally {
        if (requestGeneration === requestGenerationRef.current) setIsSubmitting(false);
      }
    },
    [commitConversation, services],
  );

  const submitMessage = useCallback(
    async (content: string) => {
      const normalizedContent = content.trim();

      if (!normalizedContent || isSubmitting) {
        return 'ignored' as const;
      }

      const now = new Date().toISOString();
      const conversationId = activeConversation?.id ?? createId('conversation');
      const userMessage: ChatMessage = {
        id: createId('user'),
        role: 'user',
        content: normalizedContent,
        createdAt: now,
        deliveryStatus: 'pending',
      };
      const conversation: ChatConversation = activeConversation
        ? {
            ...activeConversation,
            preview: truncate(normalizedContent, 100),
            updatedAt: now,
            messages: [...activeConversation.messages, userMessage],
          }
        : {
            id: conversationId,
            title: truncate(normalizedContent, 48),
            preview: truncate(normalizedContent, 100),
            createdAt: now,
            updatedAt: now,
            messages: [userMessage],
          };

      setActiveConversationId(conversationId);
      commitConversation(conversation);
      return requestAnswer(conversation, userMessage);
    },
    [activeConversation, commitConversation, isSubmitting, requestAnswer],
  );

  const retryMessage = useCallback(
    async (messageId: string) => {
      if (!activeConversation || isSubmitting) {
        return 'ignored' as const;
      }

      const failedMessage = activeConversation.messages.find(
        ({ id, role, deliveryStatus }) =>
          id === messageId && role === 'user' && deliveryStatus === 'failed',
      );

      if (!failedMessage) {
        return 'ignored' as const;
      }

      const retryConversation: ChatConversation = {
        ...activeConversation,
        updatedAt: new Date().toISOString(),
        messages: activeConversation.messages.map((message) =>
          message.id === failedMessage.id
            ? { ...message, deliveryStatus: 'pending' as const }
            : message,
        ),
      };
      const pendingMessage = retryConversation.messages.find(({ id }) => id === messageId)!;

      commitConversation(retryConversation);
      return requestAnswer(retryConversation, pendingMessage);
    },
    [activeConversation, commitConversation, isSubmitting, requestAnswer],
  );

  const startNewConversation = useCallback(() => {
    setActiveConversationId(null);
    setError(null);
    setEditorResetKey((current) => current + 1);
  }, []);

  const selectConversation = useCallback((conversationId: string) => {
    setActiveConversationId(conversationId);
    setError(null);
  }, []);

  const deleteConversation = useCallback(
    (conversationId: string) => {
      const remainingConversations = conversations.filter(({ id }) => id !== conversationId);

      try {
        services.repository.delete(conversationId);
      } catch {
        setError('Nao foi possivel excluir a conversa salva neste navegador.');
        return;
      }

      setConversations(remainingConversations);
      if (activeConversationId === conversationId) {
        setActiveConversationId(remainingConversations[0]?.id ?? null);
      }
    },
    [activeConversationId, conversations, services],
  );

  const filteredConversations = useMemo(() => {
    const normalizedQuery = normalizeSearch(searchQuery);

    if (!normalizedQuery) {
      return conversations;
    }

    return conversations.filter((conversation) =>
      normalizeSearch(
        `${conversation.title} ${conversation.messages.map(({ content }) => content).join(' ')}`,
      ).includes(normalizedQuery),
    );
  }, [conversations, searchQuery]);

  const clearError = useCallback(() => setError(null), []);

  const clearConversation = useCallback(() => {
    try {
      services.repository.clear();
    } catch {
      setError('Não foi possível limpar os dados salvos neste navegador.');
      return;
    }
    requestGenerationRef.current += 1;
    setConversations([]);
    setActiveConversationId(null);
    setSearchQuery('');
    setError(null);
    setIsSubmitting(false);
    setEditorResetKey((current) => current + 1);
  }, [services]);

  return {
    activeConversation,
    activeConversationId,
    apiStatus,
    clearError,
    clearConversation,
    conversations,
    deleteConversation,
    editorResetKey,
    error,
    filteredConversations,
    isSubmitting,
    messages: activeConversation?.messages ?? [INITIAL_GREETING],
    retryMessage,
    searchQuery,
    selectConversation,
    setSearchQuery,
    startNewConversation,
    submitMessage,
  };
}
