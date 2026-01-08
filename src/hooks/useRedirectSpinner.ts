import { useEffect, useRef } from "react";

interface RedirectSpinnerContextType {
  show: () => void;
  hide: () => void;
}

// Create a simple event-based system for managing spinner visibility across the app
let spinnerListeners: ((visible: boolean) => void)[] = [];

export const triggerSpinner = (visible: boolean) => {
  spinnerListeners.forEach((listener) => listener(visible));
};

export const useRedirectSpinner = (callback?: (visible: boolean) => void) => {
  const callbackRef = useRef(callback);

  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  useEffect(() => {
    const listener = (visible: boolean) => {
      callbackRef.current?.(visible);
    };

    spinnerListeners.push(listener);

    return () => {
      spinnerListeners = spinnerListeners.filter((l) => l !== listener);
    };
  }, []);
};

export const useNavigateWithSpinner = () => {
  return {
    showSpinner: () => triggerSpinner(true),
    hideSpinner: () => triggerSpinner(false),
  };
};
