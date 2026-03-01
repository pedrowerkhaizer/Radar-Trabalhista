import { create } from "zustand"
import type { FilterState } from "@/lib/types"

interface FilterStore {
  filters: FilterState
  setFilter: <K extends keyof FilterState>(key: K, value: FilterState[K]) => void
  resetFilters: () => void
}

const DEFAULT_FILTERS: FilterState = { meses: 12 }

export const useFiltersStore = create<FilterStore>((set) => ({
  filters: DEFAULT_FILTERS,
  setFilter: (key, value) =>
    set((state) => ({ filters: { ...state.filters, [key]: value } })),
  resetFilters: () => set({ filters: DEFAULT_FILTERS }),
}))
