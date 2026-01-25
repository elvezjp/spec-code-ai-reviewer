import { useMemo, useState } from 'react'
import { PRESET_CATALOG } from '../data/presetCatalog'
import type { Preset } from '../types'

interface UsePresetCatalogReturn {
  presets: Preset[]
  filteredPresets: Preset[]
  tags: string[]
  selectedTag: string
  setSelectedTag: (tag: string) => void
  query: string
  setQuery: (value: string) => void
  resetFilters: () => void
}

const ALL_TAG = 'all'

export function usePresetCatalog(): UsePresetCatalogReturn {
  const [selectedTag, setSelectedTag] = useState<string>(ALL_TAG)
  const [query, setQuery] = useState('')

  const tags = useMemo(() => {
    const tagSet = new Set<string>()
    PRESET_CATALOG.forEach((preset) => {
      preset.tags.forEach((tag) => tagSet.add(tag))
    })
    return [ALL_TAG, ...Array.from(tagSet)]
  }, [])

  const filteredPresets = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase()

    return PRESET_CATALOG.filter((preset) => {
      const matchesTag = selectedTag === ALL_TAG || preset.tags.includes(selectedTag)
      if (!matchesTag) return false

      if (!normalizedQuery) return true

      const haystack = [preset.name, preset.description, preset.tags.join(' ')]
        .join(' ')
        .toLowerCase()

      return haystack.includes(normalizedQuery)
    })
  }, [query, selectedTag])

  const resetFilters = () => {
    setSelectedTag(ALL_TAG)
    setQuery('')
  }

  return {
    presets: PRESET_CATALOG,
    filteredPresets,
    tags,
    selectedTag,
    setSelectedTag,
    query,
    setQuery,
    resetFilters,
  }
}

export { ALL_TAG }
