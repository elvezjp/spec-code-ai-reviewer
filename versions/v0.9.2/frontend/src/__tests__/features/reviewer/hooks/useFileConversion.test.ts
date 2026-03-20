import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useFileConversion } from '@features/reviewer/hooks/useFileConversion'

// APIモジュールのモック
vi.mock('@features/reviewer/services/api', () => ({
  fetchAvailableTools: vi.fn().mockResolvedValue([
    { name: 'mockTool', display_name: 'Mock Tool' },
  ]),
  convertExcelToMarkdown: vi.fn().mockResolvedValue({
    success: true,
    markdown: '# Converted Markdown',
  }),
  addLineNumbers: vi.fn().mockResolvedValue({
    success: true,
    content: '1: line1\n2: line2',
  }),
}))

// Fileオブジェクトのモック作成ヘルパー
function createMockFile(name: string, content = 'test content'): File {
  return new File([content], name, { type: 'text/plain' })
}

describe('useFileConversion', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('初期状態', () => {
    it('specFilesは空配列', () => {
      const { result } = renderHook(() => useFileConversion())
      expect(result.current.specFiles).toEqual([])
    })

    it('codeFilesは空配列', () => {
      const { result } = renderHook(() => useFileConversion())
      expect(result.current.codeFiles).toEqual([])
    })

    it('specMarkdownはnull', () => {
      const { result } = renderHook(() => useFileConversion())
      expect(result.current.specMarkdown).toBeNull()
    })

    it('codeWithLineNumbersはnull', () => {
      const { result } = renderHook(() => useFileConversion())
      expect(result.current.codeWithLineNumbers).toBeNull()
    })

    it('デフォルトのavailableToolsが設定されている', () => {
      const { result } = renderHook(() => useFileConversion())
      expect(result.current.availableTools).toEqual([
        { name: 'markitdown', display_name: 'MarkItDown' },
        { name: 'excel2md', display_name: 'excel2md' },
      ])
    })
  })

  describe('addSpecFiles', () => {
    it('設計書ファイルを追加できる', () => {
      const { result } = renderHook(() => useFileConversion())

      act(() => {
        result.current.addSpecFiles([createMockFile('spec1.xlsx')])
      })

      expect(result.current.specFiles).toHaveLength(1)
      expect(result.current.specFiles[0].filename).toBe('spec1.xlsx')
      expect(result.current.specFiles[0].isMain).toBe(true)
      expect(result.current.specFiles[0].type).toBe('設計書')
      expect(result.current.specFiles[0].tool).toBe('markitdown')
    })

    it('複数ファイル追加時、最初のファイルがメインになる', () => {
      const { result } = renderHook(() => useFileConversion())

      act(() => {
        result.current.addSpecFiles([
          createMockFile('spec1.xlsx'),
          createMockFile('spec2.xlsx'),
        ])
      })

      expect(result.current.specFiles).toHaveLength(2)
      expect(result.current.specFiles[0].isMain).toBe(true)
      expect(result.current.specFiles[1].isMain).toBe(false)
    })

    it('ファイル再選択時、既存ファイルはリセットされる', () => {
      const { result } = renderHook(() => useFileConversion())

      act(() => {
        result.current.addSpecFiles([createMockFile('spec1.xlsx')])
      })

      act(() => {
        result.current.addSpecFiles([createMockFile('spec2.xlsx')])
      })

      expect(result.current.specFiles).toHaveLength(1)
      expect(result.current.specFiles[0].filename).toBe('spec2.xlsx')
    })
  })

  describe('removeSpecFile', () => {
    it('指定したファイルを削除できる', () => {
      const { result } = renderHook(() => useFileConversion())

      act(() => {
        result.current.addSpecFiles([
          createMockFile('spec1.xlsx'),
          createMockFile('spec2.xlsx'),
        ])
      })

      act(() => {
        result.current.removeSpecFile('spec1.xlsx')
      })

      expect(result.current.specFiles).toHaveLength(1)
      expect(result.current.specFiles[0].filename).toBe('spec2.xlsx')
    })

    it('メインファイル削除時、次のファイルがメインになる', () => {
      const { result } = renderHook(() => useFileConversion())

      act(() => {
        result.current.addSpecFiles([
          createMockFile('spec1.xlsx'),
          createMockFile('spec2.xlsx'),
        ])
      })

      act(() => {
        result.current.removeSpecFile('spec1.xlsx')
      })

      expect(result.current.specFiles[0].isMain).toBe(true)
    })
  })

  describe('setMainSpec', () => {
    it('指定したファイルをメインに設定できる', () => {
      const { result } = renderHook(() => useFileConversion())

      act(() => {
        result.current.addSpecFiles([
          createMockFile('spec1.xlsx'),
          createMockFile('spec2.xlsx'),
        ])
      })

      act(() => {
        result.current.setMainSpec('spec2.xlsx')
      })

      expect(result.current.specFiles[0].isMain).toBe(false)
      expect(result.current.specFiles[1].isMain).toBe(true)
    })

    it('メイン変更時にステータスメッセージが設定される', () => {
      const { result } = renderHook(() => useFileConversion())

      act(() => {
        result.current.addSpecFiles([createMockFile('spec1.xlsx')])
      })

      act(() => {
        result.current.setMainSpec('spec1.xlsx')
      })

      expect(result.current.specStatus).toContain('メイン設計書が変更されました')
    })
  })

  describe('setSpecType', () => {
    it('指定したファイルの種別を変更できる', () => {
      const { result } = renderHook(() => useFileConversion())

      act(() => {
        result.current.addSpecFiles([createMockFile('spec1.xlsx')])
      })

      act(() => {
        result.current.setSpecType('spec1.xlsx', '要件定義書')
      })

      expect(result.current.specFiles[0].type).toBe('要件定義書')
    })
  })

  describe('setSpecTool', () => {
    it('指定したファイルのツールを変更できる', () => {
      const { result } = renderHook(() => useFileConversion())

      act(() => {
        result.current.addSpecFiles([createMockFile('spec1.xlsx')])
      })

      act(() => {
        result.current.setSpecTool('spec1.xlsx', 'excel2md')
      })

      expect(result.current.specFiles[0].tool).toBe('excel2md')
    })
  })

  describe('applyToolToAll', () => {
    it('全ファイルにツールを適用できる', () => {
      const { result } = renderHook(() => useFileConversion())

      act(() => {
        result.current.addSpecFiles([
          createMockFile('spec1.xlsx'),
          createMockFile('spec2.xlsx'),
        ])
      })

      act(() => {
        result.current.applyToolToAll('excel2md')
      })

      expect(result.current.specFiles[0].tool).toBe('excel2md')
      expect(result.current.specFiles[1].tool).toBe('excel2md')
    })
  })

  describe('clearSpecs', () => {
    it('設計書ファイルをクリアできる', () => {
      const { result } = renderHook(() => useFileConversion())

      act(() => {
        result.current.addSpecFiles([createMockFile('spec1.xlsx')])
      })

      act(() => {
        result.current.clearSpecs()
      })

      expect(result.current.specFiles).toEqual([])
      expect(result.current.specMarkdown).toBeNull()
      expect(result.current.specStatus).toBe('')
    })
  })

  describe('addCodeFiles', () => {
    it('コードファイルを追加できる', () => {
      const { result } = renderHook(() => useFileConversion())

      act(() => {
        result.current.addCodeFiles([createMockFile('Main.java')])
      })

      expect(result.current.codeFiles).toHaveLength(1)
      expect(result.current.codeFiles[0].filename).toBe('Main.java')
    })

    it('ファイル再選択時、既存ファイルはリセットされる', () => {
      const { result } = renderHook(() => useFileConversion())

      act(() => {
        result.current.addCodeFiles([createMockFile('Main.java')])
      })

      act(() => {
        result.current.addCodeFiles([createMockFile('App.java')])
      })

      expect(result.current.codeFiles).toHaveLength(1)
      expect(result.current.codeFiles[0].filename).toBe('App.java')
    })
  })

  describe('removeCodeFile', () => {
    it('指定したコードファイルを削除できる', () => {
      const { result } = renderHook(() => useFileConversion())

      act(() => {
        result.current.addCodeFiles([
          createMockFile('Main.java'),
          createMockFile('App.java'),
        ])
      })

      act(() => {
        result.current.removeCodeFile('Main.java')
      })

      expect(result.current.codeFiles).toHaveLength(1)
      expect(result.current.codeFiles[0].filename).toBe('App.java')
    })
  })

  describe('clearCodes', () => {
    it('コードファイルをクリアできる', () => {
      const { result } = renderHook(() => useFileConversion())

      act(() => {
        result.current.addCodeFiles([createMockFile('Main.java')])
      })

      act(() => {
        result.current.clearCodes()
      })

      expect(result.current.codeFiles).toEqual([])
      expect(result.current.codeWithLineNumbers).toBeNull()
      expect(result.current.codeStatus).toBe('')
    })
  })
})
