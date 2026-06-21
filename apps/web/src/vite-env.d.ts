/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_TECHNICAL_COPILOT_CHAT_PATH?: string;
  readonly VITE_TECHNICAL_COPILOT_CONVERSATIONS_PATH?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
