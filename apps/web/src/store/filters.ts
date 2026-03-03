import { create } from "zustand"
import type { FilterState } from "@/lib/types"

interface FilterStore {
  filters: FilterState
  committedFilters: FilterState
  setFilter: <K extends keyof FilterState>(key: K, value: FilterState[K]) => void
  commitFilters: () => void
  resetFilters: () => void
}

const DEFAULT_FILTERS: FilterState = { meses: 12 }

export const useFiltersStore = create<FilterStore>((set) => ({
  filters: DEFAULT_FILTERS,
  committedFilters: DEFAULT_FILTERS,
  setFilter: (key, value) =>
    set((state) => ({ filters: { ...state.filters, [key]: value } })),
  commitFilters: () => set((state) => ({ committedFilters: state.filters })),
  resetFilters: () => set({ filters: DEFAULT_FILTERS, committedFilters: DEFAULT_FILTERS }),
}))
