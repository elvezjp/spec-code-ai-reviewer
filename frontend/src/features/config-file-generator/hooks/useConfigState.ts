import { useState, useCallback } from 'react'
import type { LlmProvider, SpecType, SystemPromptPreset } from '@core/types'
import type { ConfigFormState, LlmFieldValues, FieldDefinition, ArrayFieldDefinition } from '../types'
import { CONFIG_SCHEMA } from '../schema/configSchema'

const DEFAULT_PROVIDER: LlmProvider = 'bedrock'

function getInitialLlmFields(provider: LlmProvider): LlmFieldValues {
  const llmSection = CONFIG_SCHEMA.sections.find((s) => s.id === 'llm')
  if (!llmSection || llmSection.outputFormat !== 'list' || !('conditional' in llmSection)) {
    return { provider, maxTokens: 10000, models: [] }
  }

  const caseConfig = llmSection.conditional.cases[provider]
  const fields: LlmFieldValues = {
    provider,
    maxTokens: 10000,
    models: [],
  }

  caseConfig.fields.forEach((field: FieldDefinition) => {
    if (field.type === 'array') {
      const arrayField = field as ArrayFieldDefinition
      fields.models = [...arrayField.defaults]
    } else if (field.type === 'number' && 'default' in field && field.default !== undefined) {
      if (field.id === 'maxTokens') {
        fields.maxTokens = field.default
      }
    } else if (field.type === 'text' && 'default' in field && field.default !== undefined) {
      if (field.id === 'region') {
        fields.region = field.default
      }
    } else if (field.type === 'fixed' && 'value' in field) {
      if (field.id === 'provider') {
        fields.provider = field.value as LlmProvider
      }
    }
  })

  return fields
}

function getInitialSpecTypes(): SpecType[] {
  const specTypesSection = CONFIG_SCHEMA.sections.find((s) => s.id === 'specTypes')
  if (!specTypesSection || specTypesSection.outputFormat !== 'table' || !('defaults' in specTypesSection)) {
    return []
  }
  return JSON.parse(JSON.stringify(specTypesSection.defaults))
}

function getInitialSystemPrompts(): SystemPromptPreset[] {
  const systemPromptsSection = CONFIG_SCHEMA.sections.find((s) => s.id === 'systemPrompts')
  if (!systemPromptsSection || systemPromptsSection.outputFormat !== 'sections' || !('defaults' in systemPromptsSection)) {
    return []
  }
  return JSON.parse(JSON.stringify(systemPromptsSection.defaults))
}

export function useConfigState() {
  const [formState, setFormState] = useState<ConfigFormState>(() => ({
    provider: DEFAULT_PROVIDER,
    llmFields: getInitialLlmFields(DEFAULT_PROVIDER),
    specTypes: getInitialSpecTypes(),
    systemPrompts: getInitialSystemPrompts(),
  }))

  // プロバイダー変更
  const handleProviderChange = useCallback((provider: LlmProvider) => {
    setFormState((prev) => ({
      ...prev,
      provider,
      llmFields: getInitialLlmFields(provider),
    }))
  }, [])

  // LLMフィールド変更
  const handleLlmFieldChange = useCallback((fieldId: string, value: string | number) => {
    setFormState((prev) => ({
      ...prev,
      llmFields: {
        ...prev.llmFields,
        [fieldId]: value,
      },
    }))
  }, [])

  // 配列アイテム変更
  const handleArrayItemChange = useCallback((index: number, value: string) => {
    setFormState((prev) => {
      const newModels = [...prev.llmFields.models]
      newModels[index] = value
      return {
        ...prev,
        llmFields: {
          ...prev.llmFields,
          models: newModels,
        },
      }
    })
  }, [])

  // 配列アイテム追加
  const handleArrayItemAdd = useCallback(() => {
    setFormState((prev) => ({
      ...prev,
      llmFields: {
        ...prev.llmFields,
        models: [...prev.llmFields.models, ''],
      },
    }))
  }, [])

  // 配列アイテム削除
  const handleArrayItemRemove = useCallback((index: number) => {
    setFormState((prev) => ({
      ...prev,
      llmFields: {
        ...prev.llmFields,
        models: prev.llmFields.models.filter((_, i) => i !== index),
      },
    }))
  }, [])

  // specTypes 行変更
  const handleSpecTypeChange = useCallback((index: number, field: keyof SpecType, value: string) => {
    setFormState((prev) => {
      const newSpecTypes = [...prev.specTypes]
      newSpecTypes[index] = {
        ...newSpecTypes[index],
        [field]: value,
      }
      return {
        ...prev,
        specTypes: newSpecTypes,
      }
    })
  }, [])

  // specTypes 行追加
  const handleSpecTypeAdd = useCallback(() => {
    setFormState((prev) => ({
      ...prev,
      specTypes: [...prev.specTypes, { type: '', note: '' }],
    }))
  }, [])

  // specTypes 行削除
  const handleSpecTypeRemove = useCallback((index: number) => {
    setFormState((prev) => ({
      ...prev,
      specTypes: prev.specTypes.filter((_, i) => i !== index),
    }))
  }, [])

  // systemPrompts アイテム変更
  const handleSystemPromptChange = useCallback(
    (index: number, field: keyof SystemPromptPreset, value: string) => {
      setFormState((prev) => {
        const newPrompts = [...prev.systemPrompts]
        newPrompts[index] = {
          ...newPrompts[index],
          [field]: value,
        }
        return {
          ...prev,
          systemPrompts: newPrompts,
        }
      })
    },
    []
  )

  // systemPrompts アイテム追加
  const handleSystemPromptAdd = useCallback(() => {
    setFormState((prev) => ({
      ...prev,
      systemPrompts: [
        ...prev.systemPrompts,
        {
          name: '',
          role: '',
          purpose: '',
          format: '',
          notes: '',
        },
      ],
    }))
  }, [])

  // systemPrompts アイテム削除
  const handleSystemPromptRemove = useCallback((index: number) => {
    setFormState((prev) => ({
      ...prev,
      systemPrompts: prev.systemPrompts.filter((_, i) => i !== index),
    }))
  }, [])

  return {
    formState,
    handleProviderChange,
    handleLlmFieldChange,
    handleArrayItemChange,
    handleArrayItemAdd,
    handleArrayItemRemove,
    handleSpecTypeChange,
    handleSpecTypeAdd,
    handleSpecTypeRemove,
    handleSystemPromptChange,
    handleSystemPromptAdd,
    handleSystemPromptRemove,
  }
}
