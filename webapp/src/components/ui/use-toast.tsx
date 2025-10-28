import * as React from 'react';

type ToastProps = {
  title: string;
  description?: string;
  variant?: 'default' | 'destructive';
};

type ToastContextType = {
  toast: (props: ToastProps) => void;
};

const ToastContext = React.createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const toast = React.useCallback((props: ToastProps) => {
  // Simple console log for now - can be replaced with actual toast UI
    console.log('[Toast]', props.title, props.description);
 }, []);

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
  </ToastContext.Provider>
  );
}

export function useToast() {
  const context = React.useContext(ToastContext);
  if (!context) {
    // Return a no-op if outside provider
    return {
      toast: (props: ToastProps) => console.log('[Toast]', props)
    };
  }
  return context;
}
