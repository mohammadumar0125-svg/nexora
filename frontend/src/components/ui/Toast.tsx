import React, { createContext, useCallback, useContext, useState } from 'react';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';

export type ToastType = 'success' | 'error' | 'info';

interface ToastItem {
  id: number;
  message: string;
  type: ToastType;
}

interface ToastContextValue {
  notify: (message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextValue>({
  notify: () => {},
});

export const useToast = () => useContext(ToastContext);

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [items, setItems] = useState<ToastItem[]>([]);

  const notify = useCallback((message: string, type: ToastType = 'info') => {
    const id = Date.now() + Math.floor(Math.random() * 1000);
    setItems((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setItems((prev) => prev.filter((item) => item.id !== id));
    }, 4500);
  }, []);

  const dismiss = (id: number) => {
    setItems((prev) => prev.filter((item) => item.id !== id));
  };

  return (
    <ToastContext.Provider value={{ notify }}>
      {children}
      <div
        aria-live="polite"
        className="fixed bottom-4 right-4 z-[60] flex flex-col gap-2 max-w-sm w-full px-4 sm:px-0 pointer-events-none"
      >
        {items.map((item) => (
          <div
            key={item.id}
            className={`pointer-events-auto flex items-start gap-3 px-4 py-3 rounded-xl border shadow-elevated text-sm font-medium bg-white ${
              item.type === 'success'
                ? 'border-[#99DDD2] text-[#127466]'
                : item.type === 'error'
                ? 'border-[#FECACA] text-[#991B1B]'
                : 'border-[#C5D5FA] text-[#202B43]'
            }`}
          >
            {item.type === 'success' && <CheckCircle2 className="w-4 h-4 mt-0.5 shrink-0 text-[#22A995]" />}
            {item.type === 'error' && <AlertCircle className="w-4 h-4 mt-0.5 shrink-0 text-[#991B1B]" />}
            {item.type === 'info' && <Info className="w-4 h-4 mt-0.5 shrink-0 text-[#3867E9]" />}
            <span className="flex-1 leading-snug">{item.message}</span>
            <button
              type="button"
              onClick={() => dismiss(item.id)}
              aria-label="Dismiss notification"
              className="text-[#5E6D87] hover:text-[#202B43] cursor-pointer"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};
