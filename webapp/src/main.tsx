import React from 'react'
import ReactDOM from 'react-dom/client'
import { Router } from './app/Router'
import './index.css'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from './lib/queryClient'

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <QueryClientProvider client={queryClient}>
     <Router />
        </QueryClientProvider>
    </React.StrictMode>,
)