import { useState, useCallback } from 'react'
import type { ConfigFormState, ValidationError, FieldDefinition } from '../types'
import { CONFIG_SCHEMA } from '../schema/configSchema'

export function useValidation() {
  const [errors, setErrors] = useState<ValidationError[]>([])

  const validate = useCallback((formState: ConfigFormState): ValidationError[] => {
    const validationErrors: ValidationError[] = []
    const llmSection = CONFIG_SCHEMA.sections.find((s) => s.id === 'llm')

    if (!llmSection || llmSection.outputFormat !== 'list' || !('conditional' in llmSection)) {
      return validationErrors
    }

    const currentCase = llmSection.conditional.cases[formState.provider]

    currentCase.fields.forEach((field: FieldDefinition) => {
      // 必須フィールドチェック
      if ('required' in field && field.required) {
        const value = formState.llmFields[field.id as keyof typeof formState.llmFields]
        if (value === undefined || value === null || (typeof value === 'string' && value.trim() === '')) {
          validationErrors.push({
            field: field.id,
            message: `${field.label || field.id}は必須です`,
          })
        }
      }

      // 数値範囲チェック
      if (field.type === 'number') {
        const value = formState.llmFields[field.id as keyof typeof formState.llmFields] as number | undefined
        if (value !== undefined) {
          if ('min' in field && field.min !== undefined && value < field.min) {
            validationErrors.push({
              field: field.id,
              message: `${field.label || field.id}は${field.min}以上にしてください`,
            })
          }
          if ('max' in field && field.max !== undefined && value > field.max) {
            validationErrors.push({
              field: field.id,
              message: `${field.label || field.id}は${field.max}以下にしてください`,
            })
          }
        }
      }
    })

    setErrors(validationErrors)
    return validationErrors
  }, [])

  const clearErrors = useCallback(() => {
    setErrors([])
  }, [])

  const getFieldError = useCallback(
    (fieldId: string): string | undefined => {
      const error = errors.find((e) => e.field === fieldId)
      return error?.message
    },
    [errors]
  )

  return {
    errors,
    validate,
    clearErrors,
    getFieldError,
  }
}
