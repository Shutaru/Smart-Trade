import { useCallback, useState } from 'react';

type Serializer<T> = (value: T) => string;
type Deserializer<T> = (value: string) => T;

const identitySerializer = <T,>(value: T): string => JSON.stringify(value);

export function useLocalStorage<T>(
  key: string,
  initialValue: T,
  deserialize: Deserializer<T> = JSON.parse as Deserializer<T>,
  serialize: Serializer<T> = identitySerializer,
): [T, (value: T) => void] {
  const [storedValue, setStoredValue] = useState<T>(() => {
    if (typeof window === 'undefined') {
      return initialValue;
    }
    try {
      const item = window.localStorage.getItem(key);
      return item ? deserialize(item) : initialValue;
    } catch (error) {
      console.warn('Failed to read localStorage key', key, error);
      return initialValue;
    }
  });

  const setValue = useCallback(
    (value: T) => {
      try {
        setStoredValue(value);
        window.localStorage.setItem(key, serialize(value));
      } catch (error) {
        console.warn('Failed to write localStorage key', key, error);
      }
    },
    [key, serialize],
  );

  return [storedValue, setValue];
}
