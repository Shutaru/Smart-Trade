import { useQuery } from '@tanstack/react-query';
import { getIndicatorOperators, type IndicatorOperatorsInfo } from '@/lib/api-lab';

/**
 * Hook to fetch recommended operators for a specific indicator
 * 
 * @param indicatorId - The indicator ID (e.g., 'rsi', 'ema')
 * @returns Query result with operator information
 * 
 * @example
 * const { data: operatorsInfo } = useIndicatorOperators('rsi');
 * // operatorsInfo.recommended_operators = ['crosses_above', 'crosses_below', '>', '<', 'between']
 * // operatorsInfo.typical_levels = { oversold: 30, overbought: 70 }
 */
export function useIndicatorOperators(indicatorId: string | null) {
  return useQuery<IndicatorOperatorsInfo | null>({
    queryKey: ['indicator-operators', indicatorId],
    queryFn: () => indicatorId ? getIndicatorOperators(indicatorId) : Promise.resolve(null),
    enabled: !!indicatorId,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes (operators don't change)
    retry: 2,
  });
}
