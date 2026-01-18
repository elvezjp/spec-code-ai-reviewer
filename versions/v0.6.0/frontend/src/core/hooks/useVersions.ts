import { useState, useCallback, useEffect } from 'react'
import type { VersionInfo } from '../types'

const COOKIE_NAME = 'app_version'

// デフォルトのバージョン情報
const DEFAULT_VERSIONS: VersionInfo[] = [
  { value: 'v0.6.0', label: 'v0.6.0', isLatest: true },
  { value: 'v0.5.2', label: 'v0.5.2', isLatest: false },
  { value: 'v0.5.1', label: 'v0.5.1', isLatest: false },
  { value: 'v0.5.0', label: 'v0.5.0', isLatest: false },
]

// Cookieヘルパー
function getCookie(name: string): string | null {
  const value = `; ${document.cookie}`
  const parts = value.split(`; ${name}=`)
  if (parts.length === 2) return parts.pop()?.split(';').shift() || null
  return null
}

function setCookie(name: string, value: string, days = 365) {
  const expires = new Date(Date.now() + days * 864e5).toUTCString()
  document.cookie = `${name}=${value}; expires=${expires}; path=/`
}

interface UseVersionsReturn {
  versions: VersionInfo[]
  currentVersion: VersionInfo
  switchVersion: (version: string) => void
  isLatest: boolean
}

export function useVersions(
  versions: VersionInfo[] = DEFAULT_VERSIONS
): UseVersionsReturn {
  const latestVersion = versions.find((v) => v.isLatest) || versions[0]

  const [currentVersion, setCurrentVersion] = useState<VersionInfo>(() => {
    const cookieVersion = getCookie(COOKIE_NAME)
    return versions.find((v) => v.value === cookieVersion) || latestVersion
  })

  // Cookie変更時の同期
  useEffect(() => {
    const cookieVersion = getCookie(COOKIE_NAME)
    const version = versions.find((v) => v.value === cookieVersion)
    if (version && version.value !== currentVersion.value) {
      setCurrentVersion(version)
    }
  }, [versions, currentVersion.value])

  const switchVersion = useCallback(
    (versionValue: string) => {
      const version = versions.find((v) => v.value === versionValue)
      if (version) {
        setCookie(COOKIE_NAME, version.value)
        setCurrentVersion(version)
        // ページをリロードしてバージョンを切り替え
        setTimeout(() => {
          window.location.reload()
        }, 800)
      }
    },
    [versions]
  )

  return {
    versions,
    currentVersion,
    switchVersion,
    isLatest: currentVersion.isLatest,
  }
}

export { DEFAULT_VERSIONS }
