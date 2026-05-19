import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Search, Trash2 } from 'lucide-react'
import { api } from '../api/client.ts'

interface Run {
  id: string
  name: string
  run_type: string
  status: string
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
  start_time: string
  end_time: string | null
  error: string | null
}

const statusColors: Record<string, string> = {
  running: 'text-warning bg-warning/10',
  success: 'text-success bg-success/10',
  error: 'text-error bg-error/10',
  created: 'text-text-muted bg-text-muted/10',
}

export default function TraceListPage() {
  const [projectName, setProjectName] = useState('')
  const [status, setStatus] = useState('')
  const [search, setSearch] = useState('')

  const { data, refetch } = useQuery({
    queryKey: ['runs', projectName, status, search],
    queryFn: () =>
      api.runs.list({
        project_name: projectName || '',
        status: status || '',
        name_contains: search || '',
        limit: 100,
      }),
  })

  const runs: Run[] = data?.runs || []

  async function handleDelete(id: string) {
    await api.runs.delete(id)
    refetch()
  }

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-text">Traces</h1>
        <span className="text-sm text-text-secondary">{data?.total ?? 0} total</span>
      </div>

      <div className="flex gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-2.5 top-2 text-text-muted" size={16} />
          <input
            type="text"
            placeholder="Search by name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 bg-surface border border-border rounded-md text-sm text-text placeholder:text-text-muted focus:outline-none focus:border-accent"
          />
        </div>
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="px-3 py-1.5 bg-surface border border-border rounded-md text-sm text-text focus:outline-none focus:border-accent"
        >
          <option value="">All statuses</option>
          <option value="running">Running</option>
          <option value="success">Success</option>
          <option value="error">Error</option>
        </select>
        <input
          type="text"
          placeholder="Project"
          value={projectName}
          onChange={(e) => setProjectName(e.target.value)}
          className="px-3 py-1.5 bg-surface border border-border rounded-md text-sm text-text placeholder:text-text-muted focus:outline-none focus:border-accent"
        />
      </div>

      <div className="border border-border rounded-lg overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-surface-hover text-text-secondary border-b border-border">
            <tr>
              <th className="px-4 py-2.5 font-medium">Name</th>
              <th className="px-4 py-2.5 font-medium">Type</th>
              <th className="px-4 py-2.5 font-medium">Status</th>
              <th className="px-4 py-2.5 font-medium">Tokens</th>
              <th className="px-4 py-2.5 font-medium">Latency</th>
              <th className="px-4 py-2.5 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {runs.map((run) => {
              const latency = run.end_time
                ? Math.round((new Date(run.end_time).getTime() - new Date(run.start_time).getTime()) / 1000)
                : '-'
              return (
                <tr key={run.id} className="hover:bg-surface-hover transition-colors">
                  <td className="px-4 py-2.5">
                    <Link to={`/traces/${run.id}`} className="text-accent hover:underline">
                      {run.name}
                    </Link>
                  </td>
                  <td className="px-4 py-2.5 text-text-secondary">{run.run_type}</td>
                  <td className="px-4 py-2.5">
                    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${statusColors[run.status] || 'text-text-muted bg-text-muted/10'}`}>
                      {run.status}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-text-secondary">{run.total_tokens.toLocaleString()}</td>
                  <td className="px-4 py-2.5 text-text-secondary">{typeof latency === 'number' ? `${latency}s` : latency}</td>
                  <td className="px-4 py-2.5 text-right">
                    <button
                      onClick={() => handleDelete(run.id)}
                      className="text-text-muted hover:text-error transition-colors"
                      title="Delete"
                    >
                      <Trash2 size={14} />
                    </button>
                  </td>
                </tr>
              )
            })}
            {runs.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-text-muted">
                  No traces found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
