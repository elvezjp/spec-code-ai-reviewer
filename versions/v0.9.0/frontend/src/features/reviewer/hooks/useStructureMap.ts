import { useState, useCallback } from 'react'
import type { StructureMapInfo, DocumentMapEntry, CodeMapEntry, DocumentPart, CodePart } from '../types'
import * as api from '../services/api'

interface UseStructureMapReturn {
  structureMap: StructureMapInfo | null
  isGenerating: boolean
  generateStructureMap: (
    specMarkdown: string,
    specFilename: string,
    codeFiles: { filename: string; content: string }[],
    existingDocumentMap: DocumentMapEntry[] | null,
    existingCodeMaps: { filename: string; entries: CodeMapEntry[] }[]
  ) => Promise<StructureMapInfo>
  clearStructureMap: () => void
}

/**
 * 構造マップ（MAP.json）を生成・管理するフック
 * useStructureMap=true の場合、レビュー実行開始時に構造マップを生成する
 * 分割プレビューで既に生成済みのものはスキップする
 */
export function useStructureMap(): UseStructureMapReturn {
  const [structureMap, setStructureMap] = useState<StructureMapInfo | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)

  /**
   * DocumentPart を DocumentMapEntry に変換
   */
  const convertToDocumentMapEntry = (part: DocumentPart, filename: string): DocumentMapEntry => ({
    id: part.id,
    section: part.section,
    level: part.level,
    path: part.path,
    original_file: filename,
    original_start_line: part.startLine,
    original_end_line: part.endLine,
    word_count: part.estimatedTokens, // 概算値として使用
    part_file: `${part.id}.md`,
    checksum: '', // バックエンドで生成される場合は空
  })

  /**
   * CodePart を CodeMapEntry に変換
   */
  const convertToCodeMapEntry = (part: CodePart, filename: string): CodeMapEntry => ({
    id: part.id,
    symbol: part.parentSymbol ? `${part.parentSymbol}#${part.symbol}` : part.symbol,
    type: part.symbolType,
    original_file: filename,
    original_start_line: part.startLine,
    original_end_line: part.endLine,
    part_file: `${part.id}.txt`,
    checksum: '', // バックエンドで生成される場合は空
  })

  /**
   * 構造マップを生成（レビュー実行開始時に呼び出す）
   * 分割プレビューで既に生成済みのものはスキップする
   */
  const generateStructureMap = useCallback(async (
    specMarkdown: string,
    specFilename: string,
    codeFiles: { filename: string; content: string }[],
    existingDocumentMap: DocumentMapEntry[] | null,
    existingCodeMaps: { filename: string; entries: CodeMapEntry[] }[]
  ): Promise<StructureMapInfo> => {
    setIsGenerating(true)

    try {
      // 1. 設計書の MAP.json（未生成の場合のみ生成）
      let documentMap: DocumentMapEntry[]
      if (existingDocumentMap && existingDocumentMap.length > 0) {
        // 分割プレビューで生成済み → スキップ
        documentMap = existingDocumentMap
      } else {
        // 未生成 → APIで生成
        const docResult = await api.splitMarkdown({
          content: specMarkdown,
          filename: specFilename,
          maxDepth: 2,
        })
        if (docResult.success && docResult.parts) {
          documentMap = docResult.parts.map((part) =>
            convertToDocumentMapEntry(part, specFilename)
          )
        } else {
          documentMap = []
        }
      }

      // 2. 各コードファイルの MAP.json（未生成のファイルのみ生成）
      const existingCodeMapFiles = new Set(existingCodeMaps.map((m) => m.filename))
      const codeMaps = await Promise.all(
        codeFiles.map(async (file) => {
          // 既に生成済みのファイルはスキップ
          const existing = existingCodeMaps.find((m) => m.filename === file.filename)
          if (existing) {
            return existing
          }
          // 未生成のファイルは新たに生成
          const codeResult = await api.splitCode({
            content: file.content,
            filename: file.filename,
          })
          if (codeResult.success && codeResult.parts) {
            return {
              filename: file.filename,
              entries: codeResult.parts.map((part) =>
                convertToCodeMapEntry(part, file.filename)
              ),
            }
          }
          return {
            filename: file.filename,
            entries: [],
          }
        })
      )

      const result: StructureMapInfo = { documentMap, codeMaps }
      setStructureMap(result)
      return result
    } finally {
      setIsGenerating(false)
    }
  }, [])

  const clearStructureMap = useCallback(() => {
    setStructureMap(null)
  }, [])

  return { structureMap, isGenerating, generateStructureMap, clearStructureMap }
}
