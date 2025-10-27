import axios from 'axios';
import { toast } from '../components/Shared/useToast';

export const api = axios.create({
  baseURL: '/',
  timeout: 15_000,
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail ?? error.message ?? 'Unexpected error';
    toast({ title: 'Request failed', description: message, variant: 'destructive' });
    return Promise.reject(error);
  },
);

export type ApiResponse<T> = {
  data: T;
};
