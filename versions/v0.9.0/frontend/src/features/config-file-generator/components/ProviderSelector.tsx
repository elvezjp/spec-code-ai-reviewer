import type { LlmProvider } from '@core/types'

interface ProviderSelectorProps {
  providers: LlmProvider[]
  selectedProvider: LlmProvider
  onProviderChange: (provider: LlmProvider) => void
}

export function ProviderSelector({ providers, selectedProvider, onProviderChange }: ProviderSelectorProps) {
  return (
    <div className="mb-6">
      <label className="block text-sm font-medium text-gray-700 mb-2">プロバイダー:</label>
      <div className="flex gap-3 flex-wrap">
        {providers.map((provider) => (
          <label
            key={provider}
            className={`inline-flex items-center px-4 py-2 border-2 rounded-lg cursor-pointer transition-all ${
              selectedProvider === provider
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-blue-300 hover:bg-blue-50'
            }`}
          >
            <input
              type="radio"
              name="provider"
              value={provider}
              checked={selectedProvider === provider}
              onChange={() => onProviderChange(provider)}
              className="mr-2"
            />
            {provider.charAt(0).toUpperCase() + provider.slice(1)}
          </label>
        ))}
      </div>
    </div>
  )
}
