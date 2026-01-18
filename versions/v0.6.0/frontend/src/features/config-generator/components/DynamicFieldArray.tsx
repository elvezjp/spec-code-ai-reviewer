interface DynamicFieldArrayProps {
  label: string
  items: string[]
  placeholder?: string
  onItemChange: (index: number, value: string) => void
  onItemAdd: () => void
  onItemRemove: (index: number) => void
}

export function DynamicFieldArray({
  label,
  items,
  placeholder,
  onItemChange,
  onItemAdd,
  onItemRemove,
}: DynamicFieldArrayProps) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">{label}:</label>
      <div className="space-y-2">
        {items.map((item, index) => (
          <div key={index} className="flex items-center gap-2">
            <input
              type="text"
              value={item}
              placeholder={placeholder}
              onChange={(e) => onItemChange(index, e.target.value)}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <button
              type="button"
              onClick={() => onItemRemove(index)}
              className="text-red-500 hover:text-red-700 px-2 py-1 text-lg"
              title="削除"
            >
              ×
            </button>
          </div>
        ))}
      </div>
      <button
        type="button"
        onClick={onItemAdd}
        className="mt-2 text-blue-500 hover:text-blue-700 text-sm flex items-center gap-1"
      >
        <span>+</span> モデルを追加
      </button>
    </div>
  )
}
