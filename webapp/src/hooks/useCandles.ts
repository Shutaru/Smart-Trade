import { useQuery } from '@tanstack/react-query';
import api from '../lib/api';

const fetchCandles = async () => {
  const { data } = await api.get('/api/candles?limit=500');
  return data.candles || []; // Corrigir para acessar o array de candles
};

export const useCandles = () => {
  return useQuery({
    queryKey: ['candles'],
    queryFn: fetchCandles,
  });
};
