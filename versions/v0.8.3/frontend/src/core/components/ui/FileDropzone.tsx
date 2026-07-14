import { useState, useRef, type DragEvent, type ChangeEvent, type ReactNode } from 'react'

interface FileDropzoneProps {
  onFilesSelect: (files: File[]) => void
  accept?: string
  multiple?: boolean
  children?: ReactNode
  placeholder?: ReactNode
  className?: string
}

export function FileDropzone({
  onFilesSelect,
  accept,
  multiple = false,
  children,
  placeholder,
  className = '',
}: FileDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)

    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      // acceptフィルタリング
      const filteredFiles = accept
        ? files.filter((file) => {
            const extensions = accept.split(',').map((ext) => ext.trim().toLowerCase())
            const fileExt = '.' + file.name.split('.').pop()?.toLowerCase()
            return extensions.some((ext) => ext === fileExt || file.type.includes(ext.replace('.', '')))
          })
        : files

      if (filteredFiles.length > 0) {
        onFilesSelect(multiple ? filteredFiles : [filteredFiles[0]])
      }
    }
  }

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    if (files.length > 0) {
      onFilesSelect(files)
    }
    // リセット
    if (inputRef.current) {
      inputRef.current.value = ''
    }
  }

  const handleClick = () => {
    inputRef.current?.click()
  }

  const defaultPlaceholder = (
    <>
      <p className="text-gray-600 mb-1">ファイルを選択</p>
      <p className="text-gray-400 text-sm">または ここにドラッグ&ドロップ</p>
    </>
  )

  return (
    <div
      className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition ${
        isDragging
          ? 'border-blue-400 bg-blue-50'
          : 'border-gray-300 hover:border-blue-400'
      } ${className}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
    >
      <input
        ref={inputRef}
        type="file"
        className="hidden"
        accept={accept}
        multiple={multiple}
        onChange={handleChange}
      />
      {children || placeholder || defaultPlaceholder}
    </div>
  )
}
