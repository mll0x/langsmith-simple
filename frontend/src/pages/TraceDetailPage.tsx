import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Clock, AlertCircle, CheckCircle } from 'lucide-react'
import { api } from '../api/client.ts'

interface Run {
  id: string
  name: string
  run_type: string
  status: string
  parent_run_id: string | null
  project_id: string
  inputs: Record<string, unknown> | null
  outputs: Record<string, unknown> | null
  error: string | null
  extra: Record<string, unknown> | null
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
  prompt_cost: string
  completion_cost: string
  start_time: string
  end_time: string | null
  first_token_at: string | null
  child_runs: Run[]
}

function JsonBlock({ data }: { data: unknown }) {
  return (
    <pre className="bg-bg border border-border rounded-md p-3 text-xs text-text-secondary overflow-auto max-h-64">
      {JSON.stringify(data, null, 2)}
    </pre>
  )
}

function SpanTree({ runs, depth = 0 }: { runs: Run[]; depth?: number }) {
  return (
    <div className="space-y-1">
      {runs.map((run) => (
        <div key={run.id}>
          <div
            className="flex items-center gap-3 py-2 px-3 rounded-md hover:bg-surface-hover transition-colors"
            style={{ paddingLeft: `${12 + depth * 24}px` }}
          >
            {run.status === 'error' ? (
              <AlertCircle size={14} className="text-error shrink-0" />
            ) : (
              <CheckCircle size={14} className="text-success shrink-0" />
            )}
            <span className="text-sm text-text font-medium">{run.name}</span>
            <span className="text-xs text-text-muted">{run.run_type}</span>
            <span className="text-xs text-text-secondary ml-auto">
              {run.total_tokens.toLocaleString()} tokens
            </span>
          </div>
          {run.child_runs?.length > 0 && <SpanTree runs={run.child_runs} depth={depth + 1} />}
        </div>
      ))}
    </div>
  )
}

export default function TraceDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data: run, isLoading } = useQuery({
    queryKey: ['run', id],
    queryFn: () => api.runs.get(id!),
    enabled: !!id,
  })

  if (isLoading) {
    return <div className="p-6 text-text-secondary">Loading...</div>
  }
  if (!run) {
    return <div className="p-6 text-error">Trace not found</div>
  }

  const latency = run.end_time
    ? Math.round((new Date(run.end_time).getTime() - new Date(run.start_time).getTime()) / 1000)
    : null

  return (
    <div className="p-6 space-y-4 max-w-5xl">
      <Link to="/traces" className="inline-flex items-center gap-1.5 text-sm text-text-secondary hover:text-text transition-colors">
        <ArrowLeft size={16} />
        Back to traces
      </Link>

      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-text">{run.name}</h1>
        <span
          className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium ${
            run.status === 'success'
              ? 'text-success bg-success/10'
              : run.status === 'error'
              ? 'text-error bg-error/10'
              : 'text-warning bg-warning/10'
          }`}
        >
          {run.status}
        </span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-surface border border-border rounded-lg p-3">
          <div className="text-xs text-text-muted mb-1">Type</div>
          <div className="text-sm text-text font-medium">{run.run_type}</div>
        </div>
        <div className="bg-surface border border-border rounded-lg p-3">
          <div className="text-xs text-text-muted mb-1">Tokens</div>
          <div className="text-sm text-text font-medium">{run.total_tokens.toLocaleString()}</div>
        </div>
        <div className="bg-surface border border-border rounded-lg p-3">
          <div className="text-xs text-text-muted mb-1">Latency</div>
          <div className="text-sm text-text font-medium flex items-center gap-1">
            <Clock size={13} />
            {latency !== null ? `${latency}s` : '-'}
          </div>
        </div>
        <div className="bg-surface border border-border rounded-lg p-3">
          <div className="text-xs text-text-muted mb-1">Cost</div>
          <div className="text-sm text-text font-medium">
            ${(Number(run.prompt_cost) + Number(run.completion_cost)).toFixed(6)}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="space-y-2">
          <h2 className="text-sm font-medium text-text-secondary">Inputs</h2>
          <JsonBlock data={run.inputs} />
        </div>
        <div className="space-y-2">
          <h2 className="text-sm font-medium text-text-secondary">Outputs</h2>
          <JsonBlock data={run.outputs} />
        </div>
      </div>

      {run.error && (
        <div className="bg-error/5 border border-error/20 rounded-lg p-3">
          <h2 className="text-sm font-medium text-error mb-1">Error</h2>
          <pre className="text-xs text-error/80 whitespace-pre-wrap">{run.error}</pre>
        </div>
      )}

      {run.child_runs && run.child_runs.length > 0 && (
        <div className="bg-surface border border-border rounded-lg p-3">
          <h2 className="text-sm font-medium text-text-secondary mb-2">Child Spans</h2>
          <SpanTree runs={run.child_runs} />
        </div>
      )}
    </div>
  )
}
