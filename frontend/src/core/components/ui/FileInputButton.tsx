import { useRef, type ChangeEvent } from 'react'

interface FileInputButtonProps {
  onFilesSelect: (files: File[]) => void
  accept?: string
  multiple?: boolean
  label?: string
  disabled?: boolean
  className?: string
}

export function FileInputButton({
  onFilesSelect,
  accept,
  multiple = false,
  label = 'ファイルを選択',
  disabled = false,
  className = '',
}: FileInputButtonProps) {
  const inputRef = useRef<HTMLInputElement>(null)

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    if (files.length > 0) {
      onFilesSelect(files)
    }
    // リセットして同じファイルを再選択可能にする
    if (inputRef.current) {
      inputRef.current.value = ''
    }
  }

  const handleClick = () => {
    inputRef.current?.click()
  }

  return (
    <label
      className={`cursor-pointer bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md transition text-sm inline-block ${
        disabled ? 'opacity-50 cursor-not-allowed' : ''
      } ${className}`}
    >
      {label}
      <input
        ref={inputRef}
        type="file"
        className="hidden"
        accept={accept}
        multiple={multiple}
        onChange={handleChange}
        disabled={disabled}
        onClick={handleClick}
      />
    </label>
  )
}
