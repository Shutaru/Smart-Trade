import { QueryClient } from '@tanstack/react-query';
import api from './api';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      refetchOnWindowFocus: false,
    },
  },
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    // TODO: Add toast notifications for errors
    return Promise.reject(error);
  }
);
