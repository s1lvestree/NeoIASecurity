import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import type { ChatMessage } from '../types/chat';
import { ticketService } from '../services/ticketService';
import { ApiError } from '../services/httpClient';
import { TechnicalCopilot } from './TechnicalCopilot';

const defaultProps = {
  conversationId: null,
  editorResetKey: 0,
  messages: [] as ChatMessage[],
  error: null,
  isSubmitting: false,
  apiStatus: 'online' as const,
  onClearError: vi.fn(),
  onClearConversation: vi.fn(),
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

    expect(screen.getByText('Detalhes técnicos')).toBeInTheDocument();
    expect(screen.queryByText('fallback')).not.toBeInTheDocument();
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

  it('cria chamado a partir da pergunta e resposta exibidas', async () => {
    const user = userEvent.setup();
    const createTicket = vi.spyOn(ticketService, 'createFromChat').mockResolvedValue({
      success: true,
      mode: 'zammad',
      ticket_id: 42,
      ticket_number: '10042',
      ticket_url: 'http://localhost:8080/#ticket/zoom/42',
      customer_email: 'cliente@example.com',
      customer_id: 7,
      created_customer: true,
      email_notification: { enabled: false, warning: false },
    });
    render(
      <TechnicalCopilot
        {...defaultProps}
        conversationId="conversation-1"
        messages={[
          {
            id: 'user-1',
            role: 'user',
            content: 'Como desbloquear o token?',
            createdAt: '2026-06-20T12:00:00.000Z',
            deliveryStatus: 'sent',
          },
          {
            id: 'assistant-1',
            role: 'assistant',
            content: 'Siga o procedimento documentado.',
            createdAt: '2026-06-20T12:01:00.000Z',
            deliveryStatus: 'sent',
          },
        ]}
      />,
    );

    await user.click(screen.getByRole('button', { name: 'Não resolveu - abrir chamado' }));

    expect(createTicket).toHaveBeenCalledWith(
      'Como desbloquear o token?',
      'Siga o procedimento documentado.',
    );
    expect(await screen.findByText('Chamado criado com sucesso no Zammad.')).toBeInTheDocument();
    expect(screen.getByText('Número do chamado: 10042')).toBeInTheDocument();
    expect(screen.getByText('Cliente: cliente@example.com')).toBeInTheDocument();
    expect(screen.getByText('Cliente criado automaticamente no Zammad.')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Abrir no Zammad/ })).toHaveAttribute(
      'href',
      'http://localhost:8080/#ticket/zoom/42',
    );
  });

  it('mostra erro amigável e diagnóstico recolhível quando o Zammad está offline', async () => {
    const user = userEvent.setup();
    vi.spyOn(ticketService, 'createFromChat').mockRejectedValue(
      new ApiError('Não foi possível conectar ao Zammad.', {
        status: 502,
        details: {
          detail: {
            message: 'Não foi possível conectar ao Zammad.',
            detail: 'Verifique ZAMMAD_BASE_URL e se o Zammad está acessível.',
          },
        },
      }),
    );
    render(
      <TechnicalCopilot
        {...defaultProps}
        conversationId="conversation-1"
        messages={[
          {
            id: 'user-1',
            role: 'user',
            content: 'Pergunta técnica',
            createdAt: '2026-06-20T12:00:00.000Z',
            deliveryStatus: 'sent',
          },
          {
            id: 'assistant-1',
            role: 'assistant',
            content: 'Resposta técnica',
            createdAt: '2026-06-20T12:01:00.000Z',
            deliveryStatus: 'sent',
          },
        ]}
      />,
    );

    await user.click(screen.getByRole('button', { name: 'Não resolveu - abrir chamado' }));

    expect(
      await screen.findByText(
        'Não foi possível criar o chamado no Zammad. Verifique a integração da plataforma de chamados.',
      ),
    ).toBeInTheDocument();
    expect(screen.getByText('Detalhes de diagnóstico')).toBeInTheDocument();
    expect(
      screen.getByText('Verifique ZAMMAD_BASE_URL e se o Zammad está acessível.'),
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Não resolveu - abrir chamado' })).toBeEnabled();
  });
});
