import { useQuery } from '@tanstack/react-query';
import api from '../lib/api';

const fetchCandles = async () => {
  const { data } = await api.get('/api/candles?limit=500');
  return data;
};

export const useCandles = () => {
  return useQuery({
    queryKey: ['candles'],
    queryFn: fetchCandles,
  });
};
