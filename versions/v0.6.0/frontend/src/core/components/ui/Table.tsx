import type { ReactNode, ThHTMLAttributes, TdHTMLAttributes } from 'react'

// Tailwind v4対応: borderを明示的にsolid指定
const tableStyles = {
  table: 'w-full border-collapse',
  thead: 'bg-gray-50',
  th: 'px-3 py-2 text-left text-sm font-medium text-gray-600 border-b border-solid border-gray-200',
  td: 'px-3 py-2 border-b border-solid border-gray-200 text-gray-800',
  // 罫線ありバリエーション（編集可能テーブル用）
  thBordered: 'px-4 py-2 text-left text-sm font-medium text-gray-700 border border-solid border-gray-200',
  tdBordered: 'border border-solid border-gray-200',
}

interface TableProps {
  children: ReactNode
  className?: string
  bordered?: boolean
}

export function Table({ children, className = '', bordered = false }: TableProps) {
  const baseClass = bordered ? `${tableStyles.table} table-fixed` : tableStyles.table
  return <table className={`${baseClass} ${className}`.trim()}>{children}</table>
}

interface TableHeadProps {
  children: ReactNode
  className?: string
}

export function TableHead({ children, className = '' }: TableHeadProps) {
  return <thead className={`${tableStyles.thead} ${className}`.trim()}>{children}</thead>
}

interface TableBodyProps {
  children: ReactNode
  className?: string
}

export function TableBody({ children, className = '' }: TableBodyProps) {
  return <tbody className={className}>{children}</tbody>
}

interface TableRowProps {
  children: ReactNode
  className?: string
}

export function TableRow({ children, className = '' }: TableRowProps) {
  return <tr className={className}>{children}</tr>
}

interface TableHeaderCellProps extends ThHTMLAttributes<HTMLTableCellElement> {
  children?: ReactNode
  className?: string
  bordered?: boolean
}

export function TableHeaderCell({
  children,
  className = '',
  bordered = false,
  ...props
}: TableHeaderCellProps) {
  const baseClass = bordered ? tableStyles.thBordered : tableStyles.th
  return (
    <th className={`${baseClass} ${className}`.trim()} {...props}>
      {children}
    </th>
  )
}

interface TableCellProps extends TdHTMLAttributes<HTMLTableCellElement> {
  children?: ReactNode
  className?: string
  bordered?: boolean
}

export function TableCell({
  children,
  className = '',
  bordered = false,
  ...props
}: TableCellProps) {
  const baseClass = bordered ? tableStyles.tdBordered : tableStyles.td
  return (
    <td className={`${baseClass} ${className}`.trim()} {...props}>
      {children}
    </td>
  )
}
