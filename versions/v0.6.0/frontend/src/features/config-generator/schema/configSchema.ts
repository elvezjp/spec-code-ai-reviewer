import type { ConfigSchema } from '../types'

export const CONFIG_SCHEMA: ConfigSchema = {
  meta: {
    outputTitle: '設計書-Javaプログラム突合 AIレビュアー 設定ファイル',
    outputFileName: 'reviewer-config.md',
    version: 'v0.6.0',
  },
  sections: [
    {
      id: 'info',
      title: 'info',
      description: '設定ファイル情報',
      outputFormat: 'list',
      fields: [
        {
          id: 'version',
          label: 'version',
          type: 'fixed',
          value: 'v0.6.0',
        },
        {
          id: 'created_at',
          label: 'created_at',
          type: 'auto',
          generator: 'timestamp_iso8601',
        },
      ],
    },
    {
      id: 'llm',
      title: 'llm',
      description: 'LLMプロバイダー設定',
      outputFormat: 'list',
      conditional: {
        switchField: 'provider',
        cases: {
          anthropic: {
            fields: [
              { id: 'provider', type: 'fixed', value: 'anthropic' },
              { id: 'apiKey', label: 'API Key', type: 'password', required: true },
              { id: 'maxTokens', label: 'Max Tokens', type: 'number', default: 16384, required: true },
              {
                id: 'models',
                label: 'モデル',
                type: 'array',
                itemType: 'text',
                placeholder: 'claude-sonnet-4-5-20250929',
                defaults: ['claude-sonnet-4-5-20250929', 'claude-haiku-4-5-20251001'],
              },
            ],
          },
          bedrock: {
            notes: [
              'モデルIDにはリージョンプレフィックス（例: us., apac., global.）が必要です。',
              'モデルによって設定可能な出力トークン上限が異なります（例: Nova系は10,000、Claude系は最大128,000）。',
              '設定可能な上限値を超えた出力トークン数を指定した場合、エラーが発生します。',
            ],
            fields: [
              { id: 'provider', type: 'fixed', value: 'bedrock' },
              { id: 'accessKeyId', label: 'Access Key ID', type: 'password', required: true },
              { id: 'secretAccessKey', label: 'Secret Access Key', type: 'password', required: true },
              { id: 'region', label: 'Region', type: 'text', default: 'ap-northeast-1', required: true },
              { id: 'maxTokens', label: 'Max Tokens', type: 'number', default: 10000, required: true },
              {
                id: 'models',
                label: 'モデル',
                type: 'array',
                itemType: 'text',
                placeholder: 'global.anthropic.claude-haiku-4-5-20251001-v1:0',
                defaults: [
                  'global.anthropic.claude-haiku-4-5-20251001-v1:0',
                  'global.anthropic.claude-sonnet-4-5-20250929-v1:0',
                  'apac.amazon.nova-pro-v1:0',
                  'apac.amazon.nova-micro-v1:0',
                ],
              },
            ],
          },
          openai: {
            fields: [
              { id: 'provider', type: 'fixed', value: 'openai' },
              { id: 'apiKey', label: 'API Key', type: 'password', required: true },
              { id: 'maxTokens', label: 'Max Tokens', type: 'number', default: 16384, required: true },
              {
                id: 'models',
                label: 'モデル',
                type: 'array',
                itemType: 'text',
                placeholder: 'gpt-5.2',
                defaults: ['gpt-5.2', 'gpt-5.2-chat-latest', 'gpt-5.2-pro', 'gpt-5.1', 'gpt-4o', 'gpt-4o-mini'],
              },
            ],
          },
        },
      },
    },
    {
      id: 'specTypes',
      title: 'specTypes',
      description: '設計書種別',
      outputFormat: 'table',
      columns: [
        { id: 'type', label: '種別', type: 'text', width: '30%' },
        { id: 'note', label: '注意事項', type: 'text', width: '70%' },
      ],
      defaults: [
        { type: '設計書', note: '機能仕様が正しく実装されているかを確認してください' },
        { type: '要件定義書', note: '要件が漏れなく実装されているかを確認してください' },
        { type: '処理ロジック', note: '処理手順やアルゴリズムが正しく実装されているかを確認してください' },
        { type: '処理フロー', note: '処理の流れが正しく実装されているかを確認してください' },
        { type: 'コーディング規約', note: 'コードがこの規約に準拠しているかを確認してください' },
        { type: 'ネーミングルール', note: '命名規則に従っているかを確認してください' },
        { type: '製造ガイド', note: 'このガイドラインに従って実装されているかを確認してください' },
        { type: '設計ガイド', note: 'この設計方針に従って実装されているかを確認してください' },
        { type: '設計書とソースのマッピング', note: 'このマッピングに基づいて突合を行ってください' },
      ],
      editable: true,
      minRows: 0,
    },
    {
      id: 'systemPrompts',
      title: 'systemPrompts',
      description: 'システムプロンプトのプリセット定義',
      outputFormat: 'sections',
      itemKey: 'name',
      fields: [
        { id: 'name', label: 'プリセット名' },
        { id: 'role', label: '役割', rows: 2 },
        { id: 'purpose', label: '目的', rows: 6 },
        { id: 'format', label: 'フォーマット', rows: 4 },
        { id: 'notes', label: '注意事項', rows: 6 },
      ],
      defaults: [
        {
          name: '標準レビュープリセット',
          role: 'あなたは設計書とプログラムコードを突合し、整合性を検証するレビュアーです。',
          purpose: `設計書の内容がプログラムに正しく実装されているかを検証し、差異や問題点を報告してください。

以下の観点でレビューを行ってください：
1. 機能網羅性: 設計書に記載された機能がコードに実装されているか
2. 仕様整合性: 関数名・変数名・データ型・処理フローが設計書と一致しているか
3. エラー処理: 設計書に記載されたエラー処理が実装されているか
4. 境界値・制約: 設計書に記載された制約条件がコードに反映されているか`,
          format: `マークダウン形式で、以下の順に出力してください：
1. サマリー（突合日時、ファイル名、総合判定）
2. 突合結果一覧（テーブル形式）
3. 詳細（問題点と推奨事項）`,
          notes: `- メイン設計書の内容について突合してください。
- 判定は「OK」「NG」「要確認」の3段階で行ってください
- 重要度が高い問題を優先して報告してください。
- 設計書を引用する際は、見出し番号や項目番号を明示してください。
- プログラムを引用する際は、行番号を必ず添えてください。
- 各設計書の冒頭に記載されている役割、種別、注意事項を考慮してください。
- メイン以外の設計書は必要な場合に参照してください。`,
        },
      ],
      editable: true,
      minRows: 0,
    },
  ],
}
