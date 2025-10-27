import { QueryClient } from '@tanstack/react-query';
import api from './api';
import { toast } from 'sonner';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
    mutations: {
      onError: (error: any) => {
        const message = error?.response?.data?.detail || error?.message || 'An error occurred';
        console.error('[Mutation Error]:', message);
        toast.error(`Error: ${message}`);
      },
    },
  },
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error?.response?.data?.detail || error?.message || 'Network error';
    console.error('[API Error]:', message, error);
    return Promise.reject(error);
  }
);
