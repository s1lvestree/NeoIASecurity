import type { GovernancePreview, GovernanceReport } from '../types/governance';
import { httpClient } from './httpClient';

const PREVIEW_PATH = '/api/governance/preview';
const REPORT_PATH = '/api/governance/report';

export const governanceService = {
  fetchPreview(days = 7, eventsPerDay = 50): Promise<GovernancePreview> {
    return httpClient.post<GovernancePreview>(PREVIEW_PATH, { days, events_per_day: eventsPerDay });
  },
  fetchReport(days = 7, eventsPerDay = 50): Promise<GovernanceReport> {
    return httpClient.post<GovernanceReport>(REPORT_PATH, { days, events_per_day: eventsPerDay });
  },
};
