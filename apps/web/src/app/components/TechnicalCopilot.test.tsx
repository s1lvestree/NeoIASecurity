import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import type { ChatMessage } from '../types/chat';
import { TechnicalCopilot } from './TechnicalCopilot';

const defaultProps = {
  conversationId: null,
  editorResetKey: 0,
  messages: [] as ChatMessage[],
  error: null,
  isSubmitting: false,
  apiStatus: 'online' as const,
  onClearError: vi.fn(),
  onSubmit: vi.fn().mockResolvedValue('sent' as const),
  onRetry: vi.fn().mockResolvedValue('sent' as const),
};

describe('TechnicalCopilot', () => {
  it('prepara o prompt do atalho sem enviar automaticamente', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn().mockResolvedValue('sent' as const);
    render(<TechnicalCopilot {...defaultProps} onSubmit={onSubmit} />);

    await user.click(screen.getByRole('button', { name: 'Logs STA' }));

    expect(
      (screen.getByRole('textbox', { name: 'Mensagem para o Copiloto' }) as HTMLTextAreaElement)
        .value,
    ).toContain('STA');
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('identifica o modo usado na resposta da IA', () => {
    render(
      <TechnicalCopilot
        {...defaultProps}
        conversationId="conversation-1"
        messages={[
          {
            id: 'assistant-1',
            role: 'assistant',
            content: 'Resposta baseada na documentacao local.',
            createdAt: '2026-06-20T12:00:00.000Z',
            deliveryStatus: 'sent',
            mode: 'fallback',
          },
        ]}
      />,
    );

    expect(screen.getByText('fallback')).toBeInTheDocument();
  });

  it('limpa e foca o editor quando editorResetKey muda sem conversa ativa', async () => {
    const user = userEvent.setup();
    const { container, rerender } = render(
      <>
        <button type="button">Fora do editor</button>
        <TechnicalCopilot {...defaultProps} />
      </>,
    );
    const editor = within(container).getByRole('textbox', { name: 'Mensagem para o Copiloto' });
    const outsideButton = within(container).getByRole('button', { name: 'Fora do editor' });

    await user.type(editor, 'rascunho ainda nao enviado');
    await user.click(outsideButton);

    expect(editor).not.toHaveFocus();

    rerender(
      <>
        <button type="button">Fora do editor</button>
        <TechnicalCopilot {...defaultProps} conversationId={null} editorResetKey={1} />
      </>,
    );

    expect(editor).toHaveValue('');
    expect(editor).toHaveFocus();

    await user.type(editor, 'novo rascunho ainda nao enviado');
    await user.click(outsideButton);

    expect(editor).not.toHaveFocus();

    rerender(
      <>
        <button type="button">Fora do editor</button>
        <TechnicalCopilot {...defaultProps} conversationId={null} editorResetKey={2} />
      </>,
    );

    expect(editor).toHaveValue('');
    expect(editor).toHaveFocus();
  });
});
