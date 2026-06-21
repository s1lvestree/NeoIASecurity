import type { ChatKpi, QuickAction, SuggestedPrompt } from '../types/chat';

export const technicalCopilotKpis: ChatKpi[] = [
  { id: 'docs', label: 'Documentacao STA', value: '45', caption: 'documentos indexados' },
  { id: 'guides', label: 'Guias DLP', value: '32', caption: 'procedimentos ativos' },
  { id: 'tickets', label: 'Chamados abertos', value: '3', caption: 'aguardando atendimento' },
  { id: 'latency', label: 'Tempo medio', value: '2,3s', caption: 'ultima medicao' },
];

export const quickActions: QuickAction[] = [
  {
    id: 'octadesk',
    label: 'Chamado Octadesk',
    accentClassName: 'text-sky-400',
    prompt: 'Prepare um resumo tecnico para abertura de chamado no Octadesk, incluindo impacto, evidencias e proximos passos.',
  },
  {
    id: 'sta',
    label: 'Logs STA',
    accentClassName: 'text-primary',
    prompt: 'Analise uma falha de autenticacao no STA e organize as hipoteses e verificacoes recomendadas.',
  },
  {
    id: 'dlp',
    label: 'DLP/Safetica',
    accentClassName: 'text-amber-400',
    prompt: 'Analise um alerta DLP/Safetica e indique evidencias, risco e tratativa recomendada.',
  },
  {
    id: 'iam',
    label: 'IAM/PAM',
    accentClassName: 'text-violet-400',
    prompt: 'Ajude a investigar um acesso IAM/PAM fora do padrao e proponha os proximos passos.',
  },
];

export const suggestedPrompts: SuggestedPrompt[] = [
  {
    id: 'prompt-1',
    title: 'Investigar comportamento de risco',
    description: 'Cruzar eventos DLP, historico do usuario e contexto da politica.',
  },
  {
    id: 'prompt-2',
    title: 'Preparar abertura de chamado',
    description: 'Estruturar resumo tecnico e checklist para revisao humana.',
  },
  {
    id: 'prompt-3',
    title: 'Consolidar troubleshooting',
    description: 'Gerar hipoteses iniciais e proximos passos com base nos logs.',
  },
];
