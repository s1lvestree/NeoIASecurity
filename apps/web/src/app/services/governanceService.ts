import type { GovernancePreview, GovernanceReport, GovernanceReportJob } from '../types/governance';
import { httpClient } from './httpClient';

const SUMMARY_PATH = '/api/governance/sta/summary';
const REPORTS_PATH = '/api/governance/reports';

export const governanceService = {
  fetchPreview(days = 7, eventsPerDay = 50): Promise<GovernancePreview> {
    void eventsPerDay;
    return httpClient.get<GovernancePreview>(`${SUMMARY_PATH}?days=${days}`);
  },
  fetchReport(days = 7, eventsPerDay = 50): Promise<GovernanceReport> {
    return httpClient.post<GovernanceReport>('/api/governance/report', { days, events_per_day: eventsPerDay });
  },
  createReport(solution = 'STA', days = 7): Promise<GovernanceReportJob> {
    return httpClient.post<GovernanceReportJob>(REPORTS_PATH, { solution, days });
  },
};
