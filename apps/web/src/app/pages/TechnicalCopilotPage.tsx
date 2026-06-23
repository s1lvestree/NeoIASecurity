import { useState } from 'react';
import { ChatHistory } from '../components/ChatHistory';
import { TechnicalCopilot } from '../components/TechnicalCopilot';
import { useTechnicalCopilotChat } from '../hooks/useTechnicalCopilotChat';

export function TechnicalCopilotPage() {
  const copilot = useTechnicalCopilotChat();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(true);

  return (
    <div className="flex h-full min-h-0 bg-background">
      <ChatHistory
        conversations={copilot.filteredConversations}
        activeConversationId={copilot.activeConversationId}
        searchQuery={copilot.searchQuery}
        onSearchChange={copilot.setSearchQuery}
        onNewConversation={copilot.startNewConversation}
        onSelectConversation={copilot.selectConversation}
        onDeleteConversation={copilot.deleteConversation}
        isCollapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed((v) => !v)}
      />

      <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
        <TechnicalCopilot
          conversationId={copilot.activeConversationId}
          editorResetKey={copilot.editorResetKey}
          messages={copilot.messages}
          error={copilot.error}
          isSubmitting={copilot.isSubmitting}
          apiStatus={copilot.apiStatus}
          onClearError={copilot.clearError}
          onClearConversation={copilot.clearConversation}
          onSubmit={copilot.submitMessage}
          onRetry={copilot.retryMessage}
        />
      </div>
    </div>
  );
}
