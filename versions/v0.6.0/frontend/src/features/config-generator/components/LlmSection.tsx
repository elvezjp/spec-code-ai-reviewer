import type { LlmProvider } from '@core/types'
import { Card } from '@core/index'
import type { ConfigFormState, LlmSectionDefinition, FieldDefinition, ArrayFieldDefinition } from '../types'
import { CONFIG_SCHEMA } from '../schema/configSchema'
import { ProviderSelector } from './ProviderSelector'
import { DynamicFieldArray } from './DynamicFieldArray'

interface LlmSectionProps {
  formState: ConfigFormState
  onProviderChange: (provider: LlmProvider) => void
  onFieldChange: (fieldId: string, value: string | number) => void
  onArrayItemChange: (index: number, value: string) => void
  onArrayItemAdd: () => void
  onArrayItemRemove: (index: number) => void
  getFieldError: (fieldId: string) => string | undefined
}

export function LlmSection({
  formState,
  onProviderChange,
  onFieldChange,
  onArrayItemChange,
  onArrayItemAdd,
  onArrayItemRemove,
  getFieldError,
}: LlmSectionProps) {
  const section = CONFIG_SCHEMA.sections.find((s) => s.id === 'llm') as LlmSectionDefinition | undefined

  if (!section || section.outputFormat !== 'list' || !('conditional' in section)) {
    return null
  }

  const providers = Object.keys(section.conditional.cases) as LlmProvider[]
  const currentCase = section.conditional.cases[formState.provider]

  const renderField = (field: FieldDefinition) => {
    if (field.type === 'fixed') return null

    const error = getFieldError(field.id)
    const value = formState.llmFields[field.id as keyof typeof formState.llmFields]
    const requiredMark = 'required' in field && field.required ? <span className="text-red-500">*</span> : null

    if (field.type === 'password' || field.type === 'text') {
      return (
        <div key={field.id}>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {field.label}: {requiredMark}
          </label>
          <input
            type={field.type}
            value={(value as string) || ''}
            placeholder={'placeholder' in field ? field.placeholder : ''}
            onChange={(e) => onFieldChange(field.id, e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          {error && <div className="text-red-500 text-sm mt-1">{error}</div>}
        </div>
      )
    }

    if (field.type === 'number') {
      return (
        <div key={field.id}>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {field.label}: {requiredMark}
          </label>
          <input
            type="number"
            value={(value as number) || 0}
            min={'min' in field ? field.min : undefined}
            max={'max' in field ? field.max : undefined}
            onChange={(e) => onFieldChange(field.id, parseInt(e.target.value) || 0)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          {error && <div className="text-red-500 text-sm mt-1">{error}</div>}
        </div>
      )
    }

    if (field.type === 'array') {
      const arrayField = field as ArrayFieldDefinition
      return (
        <DynamicFieldArray
          key={field.id}
          label={field.label || 'モデル'}
          items={formState.llmFields.models}
          placeholder={arrayField.placeholder}
          onItemChange={onArrayItemChange}
          onItemAdd={onArrayItemAdd}
          onItemRemove={onArrayItemRemove}
        />
      )
    }

    return null
  }

  return (
    <Card>
      <h2 className="text-lg font-bold text-gray-800 mb-1">■ {section.title}</h2>
      <p className="text-sm text-gray-500 mb-4">{section.description}</p>

      <ProviderSelector
        providers={providers}
        selectedProvider={formState.provider}
        onProviderChange={onProviderChange}
      />

      {currentCase.notes && currentCase.notes.length > 0 && (
        <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
          <div className="flex items-start gap-2">
            <span className="text-amber-600 text-lg">⚠</span>
            <div>
              <p className="font-medium text-amber-800 mb-1">注意</p>
              <ul className="text-sm text-amber-700 space-y-1">
                {currentCase.notes.map((note, index) => (
                  <li key={index}>• {note}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      <div className="space-y-4">{currentCase.fields.map(renderField)}</div>
    </Card>
  )
}
