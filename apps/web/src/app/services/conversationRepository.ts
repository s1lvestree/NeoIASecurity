import type { ChatConversation, ChatMessage } from '../types/chat';

export const LOCAL_STORAGE_CONVERSATIONS_KEY = 'neoia.chat.v2.conversations';
const STORAGE_VERSION = 2;
const LEGACY_STORAGE_KEYS = ['neoia.technicalCopilot.v1', 'neoia.chat.conversations'];

type StorageAdapter = Pick<Storage, 'getItem' | 'setItem' | 'removeItem'>;

interface StoredConversations {
  version: typeof STORAGE_VERSION;
  conversations: ChatConversation[];
}

export interface ConversationRepository {
  list(): ChatConversation[];
  save(conversation: ChatConversation): void;
  delete(conversationId: string): void;
  clear(): void;
}

function isMessage(value: unknown): value is ChatMessage {
  if (!value || typeof value !== 'object') {
    return false;
  }

  const message = value as Partial<ChatMessage>;
  return (
    typeof message.id === 'string' &&
    (message.role === 'assistant' || message.role === 'user' || message.role === 'system') &&
    typeof message.content === 'string' &&
    typeof message.createdAt === 'string' &&
    (message.deliveryStatus === 'pending' ||
      message.deliveryStatus === 'sent' ||
      message.deliveryStatus === 'failed')
  );
}

function isConversation(value: unknown): value is ChatConversation {
  if (!value || typeof value !== 'object') {
    return false;
  }

  const conversation = value as Partial<ChatConversation>;
  return (
    typeof conversation.id === 'string' &&
    typeof conversation.title === 'string' &&
    typeof conversation.preview === 'string' &&
    typeof conversation.createdAt === 'string' &&
    typeof conversation.updatedAt === 'string' &&
    Array.isArray(conversation.messages) &&
    conversation.messages.every(isMessage)
  );
}

function sortByRecent(conversations: ChatConversation[]) {
  return [...conversations].sort((left, right) => right.updatedAt.localeCompare(left.updatedAt));
}

export class LocalStorageConversationRepository implements ConversationRepository {
  constructor(
    private readonly storage: StorageAdapter = window.localStorage,
    private readonly sessionStorage: StorageAdapter | null = window.sessionStorage,
  ) {}

  list() {
    const rawValue = this.storage.getItem(LOCAL_STORAGE_CONVERSATIONS_KEY);

    if (!rawValue) {
      return [];
    }

    try {
      const payload = JSON.parse(rawValue) as Partial<StoredConversations>;

      if (
        payload.version !== STORAGE_VERSION ||
        !Array.isArray(payload.conversations) ||
        !payload.conversations.every(isConversation)
      ) {
        return [];
      }

      return sortByRecent(payload.conversations);
    } catch {
      return [];
    }
  }

  save(conversation: ChatConversation) {
    const conversations = sortByRecent([
      conversation,
      ...this.list().filter(({ id }) => id !== conversation.id),
    ]);
    this.write(conversations);
  }

  delete(conversationId: string) {
    this.write(this.list().filter(({ id }) => id !== conversationId));
  }

  clear() {
    for (const key of [LOCAL_STORAGE_CONVERSATIONS_KEY, ...LEGACY_STORAGE_KEYS]) {
      this.storage.removeItem(key);
      this.sessionStorage?.removeItem(key);
    }
  }

  private write(conversations: ChatConversation[]) {
    const payload: StoredConversations = {
      version: STORAGE_VERSION,
      conversations,
    };

    this.storage.setItem(LOCAL_STORAGE_CONVERSATIONS_KEY, JSON.stringify(payload));
  }
}
