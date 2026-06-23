import { act, renderHook, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { ChatConversation, ChatMessage } from '../types/chat';
import type { ChatService } from '../services/chatService';
import type { ConversationRepository } from '../services/conversationRepository';
import type { HealthService } from '../services/healthService';
import { useTechnicalCopilotChat } from './useTechnicalCopilotChat';

class MemoryConversationRepository implements ConversationRepository {
  conversations: ChatConversation[] = [];

  list() {
    return [...this.conversations].sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
  }

  save(conversation: ChatConversation) {
    this.conversations = [
      conversation,
      ...this.conversations.filter(({ id }) => id !== conversation.id),
    ];
  }

  delete(conversationId: string) {
    this.conversations = this.conversations.filter(({ id }) => id !== conversationId);
  }

  clear() {
    this.conversations = [];
  }
}

const healthService: HealthService = {
  check: vi.fn().mockResolvedValue({ status: 'online' }),
};

function assistantMessage(content = 'Resposta da IA'): ChatMessage {
  return {
    id: 'assistant-1',
    role: 'assistant',
    content,
    createdAt: '2026-06-20T12:01:00.000Z',
    deliveryStatus: 'sent',
    mode: 'bedrock',
  };
}

describe('useTechnicalCopilotChat', () => {
  it('limpa todas as conversas e restaura somente a saudacao inicial', () => {
    const repository = new MemoryConversationRepository();
    repository.conversations = [{
      id: 'old', title: 'Antiga', preview: 'Antiga',
      createdAt: '2026-06-20T10:00:00.000Z', updatedAt: '2026-06-20T10:00:00.000Z', messages: [],
    }];
    const { result } = renderHook(() => useTechnicalCopilotChat({
      repository, chatService: { sendMessage: vi.fn() }, healthService,
    }));

    act(() => result.current.clearConversation());

    expect(result.current.conversations).toEqual([]);
    expect(result.current.messages).toHaveLength(1);
    expect(result.current.messages[0].role).toBe('assistant');
    expect(repository.conversations).toEqual([]);
  });

  it('emite um novo reset a cada solicitacao de nova conversa', () => {
    const repository = new MemoryConversationRepository();
    const chatService: ChatService = { sendMessage: vi.fn() };
    const { result } = renderHook(() =>
      useTechnicalCopilotChat({ repository, chatService, healthService }),
    );
    expect(result.current.editorResetKey).toBe(0);
    act(() => result.current.startNewConversation());
    expect(result.current.editorResetKey).toBe(1);
    act(() => result.current.startNewConversation());
    expect(result.current.editorResetKey).toBe(2);
    expect(repository.conversations).toEqual([]);
  });

  it('cria e persiste uma conversa somente no primeiro envio', async () => {
    const repository = new MemoryConversationRepository();
    const chatService: ChatService = {
      sendMessage: vi.fn().mockResolvedValue(assistantMessage()),
    };
    const { result } = renderHook(() =>
      useTechnicalCopilotChat({ repository, chatService, healthService }),
    );

    expect(result.current.conversations).toEqual([]);
    expect(result.current.activeConversationId).toBeNull();

    await act(async () => {
      await result.current.submitMessage('Como investigar uma falha de MFA?');
    });

    expect(repository.conversations).toHaveLength(1);
    expect(repository.conversations[0].title).toContain('Como investigar uma falha');
    expect(repository.conversations[0].messages.map(({ role }) => role)).toEqual([
      'user',
      'assistant',
    ]);
  });

  it('busca no titulo e no conteudo e seleciona a conversa mais recente apos excluir', () => {
    const repository = new MemoryConversationRepository();
    repository.conversations = [
      {
        id: 'sta',
        title: 'Falha no STA',
        preview: 'MFA bloqueado',
        createdAt: '2026-06-20T10:00:00.000Z',
        updatedAt: '2026-06-20T10:00:00.000Z',
        messages: [{
          id: 'm1',
          role: 'user',
          content: 'Erro de autenticacao multifator',
          createdAt: '2026-06-20T10:00:00.000Z',
          deliveryStatus: 'sent',
        }],
      },
      {
        id: 'dlp',
        title: 'Politica DLP',
        preview: 'Safetica',
        createdAt: '2026-06-19T10:00:00.000Z',
        updatedAt: '2026-06-19T10:00:00.000Z',
        messages: [],
      },
    ];
    const chatService: ChatService = { sendMessage: vi.fn() };
    const { result } = renderHook(() =>
      useTechnicalCopilotChat({ repository, chatService, healthService }),
    );

    act(() => result.current.setSearchQuery('multifator'));
    expect(result.current.filteredConversations.map(({ id }) => id)).toEqual(['sta']);

    act(() => result.current.deleteConversation('sta'));
    expect(result.current.activeConversationId).toBe('dlp');
  });

  it('mantem a pergunta com erro e faz retry sem duplica-la', async () => {
    const repository = new MemoryConversationRepository();
    const sendMessage = vi
      .fn()
      .mockRejectedValueOnce(new Error('API indisponivel'))
      .mockResolvedValueOnce(assistantMessage());
    const chatService: ChatService = { sendMessage };
    const { result } = renderHook(() =>
      useTechnicalCopilotChat({ repository, chatService, healthService }),
    );

    await act(async () => {
      await result.current.submitMessage('Verifique o acesso');
    });

    const failedMessage = result.current.messages[0];
    expect(failedMessage.deliveryStatus).toBe('failed');

    await act(async () => {
      await result.current.retryMessage(failedMessage.id);
    });

    await waitFor(() => expect(result.current.messages).toHaveLength(2));
    expect(result.current.messages.filter(({ role }) => role === 'user')).toHaveLength(1);
    expect(result.current.messages[0].deliveryStatus).toBe('sent');
  });
});
