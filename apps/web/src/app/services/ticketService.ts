import { httpClient } from './httpClient';

export interface TicketResponse {
  success: boolean;
  mode: string;
  ticket_id: number | string | null;
  ticket_number: number | string | null;
  ticket_url: string | null;
  customer_email?: string | null;
  customer_id?: number | string | null;
  created_customer?: boolean;
  email_notification?: {
    enabled: boolean;
    warning: boolean;
  };
}

export const ticketService = {
  createFromChat(question: string, answer: string) {
    return httpClient.post<TicketResponse>('/api/tickets/from-chat', { question, answer });
  },
};
