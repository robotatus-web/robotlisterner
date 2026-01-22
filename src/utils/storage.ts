const STORAGE_PREFIX = 'accounting_';

export function saveToStorage<T>(key: string, data: T): void {
  try {
    localStorage.setItem(STORAGE_PREFIX + key, JSON.stringify(data));
  } catch (error) {
    console.error(`Failed to save ${key} to storage:`, error);
  }
}

export function loadFromStorage<T>(key: string, defaultValue: T): T {
  try {
    const stored = localStorage.getItem(STORAGE_PREFIX + key);
    if (stored) {
      return JSON.parse(stored) as T;
    }
  } catch (error) {
    console.error(`Failed to load ${key} from storage:`, error);
  }
  return defaultValue;
}

export function removeFromStorage(key: string): void {
  try {
    localStorage.removeItem(STORAGE_PREFIX + key);
  } catch (error) {
    console.error(`Failed to remove ${key} from storage:`, error);
  }
}
