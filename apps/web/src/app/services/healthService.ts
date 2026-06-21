import type { ApiHealthStatus } from '../types/chat';
import { httpClient } from './httpClient';

export interface HealthSnapshot {
  status: Exclude<ApiHealthStatus, 'checking'>;
}

export interface HealthService {
  check(): Promise<HealthSnapshot>;
}

export const apiHealthService: HealthService = {
  async check() {
    try {
      await httpClient.get('/health');
      return { status: 'online' };
    } catch {
      return { status: 'offline' };
    }
  },
};
