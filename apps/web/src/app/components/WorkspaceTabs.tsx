import { useState } from 'react';
import { Sparkles, Shield } from 'lucide-react';
import { TechnicalCopilotPage } from '../pages/TechnicalCopilotPage';
import { GovernanceAI } from './GovernanceAI';

export function WorkspaceTabs() {
  const [activeTab, setActiveTab] = useState<'technical' | 'governance'>('technical');

  return (
    <div className="flex flex-col h-full">
      <div className="flex gap-2 mb-6 border-b border-border">
        <button
          onClick={() => setActiveTab('technical')}
          className={`flex items-center gap-2 px-6 py-3 border-b-2 transition-colors ${
            activeTab === 'technical'
              ? 'border-primary text-primary'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <Sparkles className="w-4 h-4" />
          <span className="font-medium">Technical Copilot</span>
          <span className="text-xs px-2 py-0.5 bg-primary/10 text-primary rounded-md">
            Ala Técnica
          </span>
        </button>
        <button
          onClick={() => setActiveTab('governance')}
          className={`flex items-center gap-2 px-6 py-3 border-b-2 transition-colors ${
            activeTab === 'governance'
              ? 'border-primary text-primary'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <Shield className="w-4 h-4" />
          <span className="font-medium">Governance AI</span>
          <span className="text-xs px-2 py-0.5 bg-primary/10 text-primary rounded-md">
            Ala Governança
          </span>
        </button>
      </div>

      <div className="flex-1 overflow-hidden">
        {activeTab === 'technical' ? <TechnicalCopilotPage /> : <GovernanceAI />}
      </div>
    </div>
  );
}
