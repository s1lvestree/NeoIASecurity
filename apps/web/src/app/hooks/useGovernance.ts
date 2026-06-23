import { useCallback, useEffect, useState } from 'react';
import type { GovernancePreview, GovernanceReport, GovernanceReportJob } from '../types/governance';
import { governanceService } from '../services/governanceService';

interface GovernanceState {
  preview: GovernancePreview | null;
  loading: boolean;
  error: string | null;
  fetchReport: () => Promise<GovernanceReport | null>;
  createReport: (solution: 'STA', days: number) => Promise<GovernanceReportJob | null>;
  refresh: () => void;
}

export function useGovernance(days = 7, eventsPerDay = 50): GovernanceState {
  const [preview, setPreview] = useState<GovernancePreview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await governanceService.fetchPreview(days, eventsPerDay);
      setPreview(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar dados de governança.');
    } finally {
      setLoading(false);
    }
  }, [days, eventsPerDay]);

  useEffect(() => {
    load();
  }, [load]);

  const fetchReport = useCallback(async (): Promise<GovernanceReport | null> => {
    try {
      return await governanceService.fetchReport(days, eventsPerDay);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao gerar relatório.');
      return null;
    }
  }, [days, eventsPerDay]);

  const createReport = useCallback(async (solution: 'STA', reportDays: number): Promise<GovernanceReportJob | null> => {
    try {
      return await governanceService.createReport(solution, reportDays);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao gerar relatório PDF.');
      throw err;
    }
  }, []);

  return { preview, loading, error, fetchReport, createReport, refresh: load };
}
