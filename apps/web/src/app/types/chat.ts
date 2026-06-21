export type ChatRole = 'assistant' | 'user' | 'system';
export type ChatDeliveryStatus = 'pending' | 'sent' | 'failed';
export type ChatResponseMode = 'bedrock' | 'fallback';
export type ApiHealthStatus = 'checking' | 'online' | 'offline';

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  createdAt: string;
  deliveryStatus: ChatDeliveryStatus;
  mode?: ChatResponseMode;
  references?: string[];
}

export interface ChatConversation {
  id: string;
  title: string;
  preview: string;
  createdAt: string;
  updatedAt: string;
  messages: ChatMessage[];
}

export interface ChatKpi {
  id: string;
  label: string;
  value: string;
  caption: string;
}

export interface QuickAction {
  id: string;
  label: string;
  accentClassName: string;
  prompt: string;
}

export interface SuggestedPrompt {
  id: string;
  title: string;
  description: string;
}
