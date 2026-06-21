import { beforeEach, describe, expect, it } from 'vitest';
import type { ChatConversation } from '../types/chat';
import {
  LOCAL_STORAGE_CONVERSATIONS_KEY,
  LocalStorageConversationRepository,
} from './conversationRepository';

const olderConversation: ChatConversation = {
  id: 'older',
  title: 'Conversa antiga',
  preview: 'Primeira conversa',
  createdAt: '2026-06-19T10:00:00.000Z',
  updatedAt: '2026-06-19T10:00:00.000Z',
  messages: [],
};

const newerConversation: ChatConversation = {
  ...olderConversation,
  id: 'newer',
  title: 'Conversa recente',
  updatedAt: '2026-06-20T10:00:00.000Z',
};

describe('LocalStorageConversationRepository', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('persiste conversas e retorna as mais recentes primeiro', () => {
    const repository = new LocalStorageConversationRepository(localStorage);

    repository.save(olderConversation);
    repository.save(newerConversation);

    expect(repository.list().map(({ id }) => id)).toEqual(['newer', 'older']);
  });

  it('retorna vazio quando os dados persistidos sao invalidos', () => {
    localStorage.setItem(LOCAL_STORAGE_CONVERSATIONS_KEY, '{invalido');
    const repository = new LocalStorageConversationRepository(localStorage);

    expect(repository.list()).toEqual([]);
  });

  it('remove somente a conversa solicitada', () => {
    const repository = new LocalStorageConversationRepository(localStorage);
    repository.save(olderConversation);
    repository.save(newerConversation);

    repository.delete('newer');

    expect(repository.list()).toEqual([olderConversation]);
  });
});
