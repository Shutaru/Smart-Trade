import { createContext, ReactNode, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { cn } from '../../lib/cn';
import { Button } from '../ui/button';

export type ToastVariant = 'default' | 'destructive';

export type ToastOptions = {
  id?: string;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  duration?: number;
  variant?: ToastVariant;
};

type ToastEntry = ToastOptions & { id: string };

type ToastContextValue = {
  toasts: ToastEntry[];
  toast: (options: ToastOptions) => void;
  dismiss: (id: string) => void;
};

declare global {
  interface Window {
    __toast?: ToastContextValue;
  }
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

const randomId = () => Math.random().toString(36).slice(2);

export const ToastProvider = ({ children }: { children: ReactNode }): JSX.Element => {
  const [toasts, setToasts] = useState<ToastEntry[]>([]);

  const dismiss = useCallback((id: string) => {
    setToasts((current) => current.filter((toastItem) => toastItem.id !== id));
  }, []);

  const showToast = useCallback(
    (options: ToastOptions) => {
      const id = options.id ?? randomId();
      setToasts((current) => [...current.filter((toastItem) => toastItem.id !== id), { ...options, id }]);
      if (options.duration !== 0) {
        window.setTimeout(() => dismiss(id), options.duration ?? 4000);
      }
    },
    [dismiss],
  );

  const value = useMemo(() => ({ toasts, toast: showToast, dismiss }), [dismiss, showToast, toasts]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="pointer-events-none fixed inset-0 z-[60] flex flex-col items-end gap-2 p-4 sm:p-6">
        {toasts.map(({ id, title, description, actionLabel, onAction, variant = 'default' }) => (
          <div
            key={id}
            role="status"
            className={cn(
              'pointer-events-auto w-full max-w-sm rounded-2xl border border-border bg-surface p-4 shadow-card transition-all',
              variant === 'destructive' && 'border-rose-500/50 bg-rose-500/10 text-rose-200',
            )}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-white">{title}</p>
                {description ? <p className="mt-1 text-sm text-slate-300">{description}</p> : null}
              </div>
              <div className="flex items-center gap-2">
                {actionLabel && onAction ? (
                  <Button
                    size="sm"
                    variant={variant === 'destructive' ? 'ghost' : 'outline'}
                    onClick={() => {
                      onAction();
                      dismiss(id);
                    }}
                  >
                    {actionLabel}
                  </Button>
                ) : null}
                <Button size="sm" variant="ghost" onClick={() => dismiss(id)}>
                  Close
                </Button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = (): ToastContextValue => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};

export const toast = (options: ToastOptions) => {
  if (typeof window === 'undefined') return;
  if (window.__toast) {
    window.__toast.toast(options);
    return;
  }
  window.dispatchEvent(new CustomEvent('smart-trade-toast', { detail: options }));
};

if (typeof window !== 'undefined') {
  window.addEventListener('smart-trade-toast', (event: Event) => {
    const customEvent = event as CustomEvent<ToastOptions>;
    window.__toast?.toast(customEvent.detail);
  });
}

export const ToastBridge = ({ children }: { children: ReactNode }): JSX.Element => {
  const context = useToast();

  useEffect(() => {
    window.__toast = context;
    return () => {
      if (window.__toast === context) {
        window.__toast = undefined;
      }
    };
  }, [context]);

  return <>{children}</>;
};
