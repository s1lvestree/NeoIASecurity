import type { ChatMessage, ChatResponseMode, ChatRole } from '../types/chat';
import { httpClient } from './httpClient';

const DEFAULT_CHAT_PATH = '/api/technical-copilot/chat';

function getChatPath() {
  return import.meta.env.VITE_TECHNICAL_COPILOT_CHAT_PATH?.trim() || DEFAULT_CHAT_PATH;
}

function normalizeRole(role: unknown, fallbackRole: ChatRole = 'assistant'): ChatRole {
  if (role === 'assistant' || role === 'user' || role === 'system') {
    return role;
  }

  return fallbackRole;
}

function normalizeReferences(references: unknown) {
  if (!Array.isArray(references)) {
    return undefined;
  }

  const normalizedReferences = references.filter(
    (reference): reference is string => typeof reference === 'string' && reference.trim().length > 0,
  );

  return normalizedReferences.length > 0 ? normalizedReferences : undefined;
}

function normalizeMode(value: unknown): ChatResponseMode | undefined {
  return value === 'bedrock' || value === 'fallback' ? value : undefined;
}

function readMessageContent(payload: Record<string, unknown>) {
  const candidates = [
    payload.content,
    payload.answer,
    payload.response,
    payload.message,
    payload.output_text,
    payload.text,
  ];

  const content = candidates.find(
    (candidate): candidate is string => typeof candidate === 'string' && candidate.trim().length > 0,
  );

  return content?.trim();
}

function toChatMessage(payload: Record<string, unknown>, fallbackRole: ChatRole = 'assistant') {
  const content = readMessageContent(payload);

  if (!content) {
    return null;
  }

  return {
    id:
      (typeof payload.id === 'string' && payload.id) ||
      `${fallbackRole}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    role: normalizeRole(payload.role, fallbackRole),
    content,
    createdAt: new Date().toISOString(),
    deliveryStatus: 'sent',
    mode: normalizeMode(payload.mode),
    references: normalizeReferences(payload.references),
  } satisfies ChatMessage;
}

function extractMessages(payload: unknown): ChatMessage[] {
  if (Array.isArray(payload)) {
    return payload
      .map((entry) => (entry && typeof entry === 'object' ? toChatMessage(entry as Record<string, unknown>) : null))
      .filter((message): message is ChatMessage => Boolean(message));
  }

  if (!payload || typeof payload !== 'object') {
    return [];
  }

  const record = payload as Record<string, unknown>;
  const nestedMessages = record.messages ?? record.data ?? record.items;

  return extractMessages(nestedMessages);
}

function extractAssistantMessage(payload: unknown): ChatMessage {
  if (!payload || typeof payload !== 'object') {
    throw new Error('Resposta da API em formato inesperado.');
  }

  const record = payload as Record<string, unknown>;
  const nestedCandidates = [record.message, record.assistant_message, record.assistant, record.data];

  for (const candidate of nestedCandidates) {
    if (candidate && typeof candidate === 'object') {
      const message = toChatMessage(candidate as Record<string, unknown>, 'assistant');
      if (message) {
        return message;
      }
    }
  }

  const directMessage = toChatMessage(record, 'assistant');
  if (directMessage) {
    return directMessage;
  }

  const messages = extractMessages(record.messages);
  const lastAssistantMessage = [...messages].reverse().find((message) => message.role === 'assistant');

  if (lastAssistantMessage) {
    return lastAssistantMessage;
  }

  throw new Error('Resposta da API sem mensagem utilizavel.');
}

export interface SendMessageInput {
  conversationId: string;
  content: string;
}

export interface ChatService {
  sendMessage(input: SendMessageInput): Promise<ChatMessage>;
}

export const apiChatService: ChatService = {
  async sendMessage(input) {
    const payload = await httpClient.post<unknown>(getChatPath(), {
      conversation_id: input.conversationId,
      conversationId: input.conversationId,
      content: input.content,
      message: input.content,
    });

    return extractAssistantMessage(payload);
  },
};
