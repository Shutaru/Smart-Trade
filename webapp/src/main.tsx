import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import App from './app/App';
import './styles/index.css';
import { queryClient } from './state/queryClient';
import { ThemeProvider } from './components/Shared/ThemeProvider';
import { ToastProvider, ToastBridge } from './components/Shared/useToast';

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <ToastBridge>
          <ThemeProvider>
            <BrowserRouter>
              <App />
            </BrowserRouter>
          </ThemeProvider>
        </ToastBridge>
      </ToastProvider>
    </QueryClientProvider>
  </React.StrictMode>,
);
