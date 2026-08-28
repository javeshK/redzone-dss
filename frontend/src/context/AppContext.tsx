import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  ReactNode,
} from 'react';
import { getDistrict, isUsingApi, resetApiCheck } from '../api/client';
import { DEFAULT_LAYERS, LayerVisibility, HabitationSummary, MetaResponse } from '../types';

export type DataSource = 'loading' | 'api' | 'static';

interface AppContextValue {
  selectedHabitationId: string | null;
  setSelectedHabitationId: (id: string | null) => void;
  layers: LayerVisibility;
  setLayers: (layers: LayerVisibility) => void;
  toggleLayer: (key: keyof LayerVisibility) => void;
  habitations: HabitationSummary[];
  setHabitations: (h: HabitationSummary[]) => void;
  meta: MetaResponse | null;
  dataSource: DataSource;
  refreshAppData: () => Promise<void>;
}

const AppContext = createContext<AppContextValue | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [selectedHabitationId, setSelectedHabitationId] = useState<string | null>(null);
  const [layers, setLayers] = useState<LayerVisibility>(DEFAULT_LAYERS);
  const [habitations, setHabitations] = useState<HabitationSummary[]>([]);
  const [meta, setMeta] = useState<MetaResponse | null>(null);
  const [dataSource, setDataSource] = useState<DataSource>('loading');

  const refreshAppData = useCallback(async () => {
    resetApiCheck();
    setDataSource('loading');
    try {
      const district = await getDistrict();
      setMeta(district.meta);
      setDataSource(isUsingApi() ? 'api' : 'static');
    } catch {
      setDataSource('static');
    }
  }, []);

  useEffect(() => {
    refreshAppData();
  }, [refreshAppData]);

  const toggleLayer = useCallback((key: keyof LayerVisibility) => {
    setLayers((prev) => ({ ...prev, [key]: !prev[key] }));
  }, []);

  return (
    <AppContext.Provider
      value={{
        selectedHabitationId,
        setSelectedHabitationId,
        layers,
        setLayers,
        toggleLayer,
        habitations,
        setHabitations,
        meta,
        dataSource,
        refreshAppData,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used within AppProvider');
  return ctx;
}
