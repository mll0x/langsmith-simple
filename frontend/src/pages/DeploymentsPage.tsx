import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Rocket, Square, Trash2, Terminal, Plus } from 'lucide-react'
import { api } from '../api/client.ts'

interface Deployment {
  id: string
  name: string
  config_path: string
  source_type: string
  status: string
  container_url: string | null
  port: number | null
  pid: number | null
  command: string | null
  created_at: string
}

const statusColors: Record<string, string> = {
  running: 'text-success bg-success/10',
  stopped: 'text-text-muted bg-text-muted/10',
  created: 'text-info bg-info/10',
  error: 'text-error bg-error/10',
}

export default function DeploymentsPage() {
  const queryClient = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [newName, setNewName] = useState('')
  const [newPath, setNewPath] = useState('')
  const [newCommand, setNewCommand] = useState('')
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const { data } = useQuery({
    queryKey: ['deployments'],
    queryFn: () => api.deployments.list(),
  })

  const deployments: Deployment[] = data || []

  const createMutation = useMutation({
    mutationFn: (body: object) => api.deployments.create(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deployments'] })
      setShowCreate(false)
      setNewName('')
      setNewPath('')
      setNewCommand('')
    },
  })

  const startMutation = useMutation({
    mutationFn: (id: string) => api.deployments.start(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['deployments'] }),
  })

  const stopMutation = useMutation({
    mutationFn: (id: string) => api.deployments.stop(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['deployments'] }),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deployments.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deployments'] })
      setSelectedId(null)
    },
  })

  const { data: logsData } = useQuery({
    queryKey: ['deployment-logs', selectedId],
    queryFn: () => api.deployments.logs(selectedId!),
    enabled: !!selectedId,
    refetchInterval: 3000,
  })

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-text">Deployments</h1>
        <button
          onClick={() => setShowCreate(true)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-accent hover:bg-accent-hover text-white rounded-md text-sm font-medium transition-colors"
        >
          <Plus size={14} />
          New Deployment
        </button>
      </div>

      {showCreate && (
        <div className="bg-surface border border-border rounded-lg p-4 space-y-3">
          <h2 className="text-sm font-medium text-text">Create Deployment</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <input
              placeholder="Name"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              className="px-3 py-1.5 bg-bg border border-border rounded-md text-sm text-text placeholder:text-text-muted focus:outline-none focus:border-accent"
            />
            <input
              placeholder="Config path (dir or file)"
              value={newPath}
              onChange={(e) => setNewPath(e.target.value)}
              className="px-3 py-1.5 bg-bg border border-border rounded-md text-sm text-text placeholder:text-text-muted focus:outline-none focus:border-accent"
            />
            <input
              placeholder="Command (optional)"
              value={newCommand}
              onChange={(e) => setNewCommand(e.target.value)}
              className="px-3 py-1.5 bg-bg border border-border rounded-md text-sm text-text placeholder:text-text-muted focus:outline-none focus:border-accent"
            />
          </div>
          <div className="flex gap-2">
            <button
              onClick={() =>
                createMutation.mutate({
                  name: newName,
                  config_path: newPath,
                  command: newCommand || undefined,
                })
              }
              className="px-3 py-1.5 bg-accent hover:bg-accent-hover text-white rounded-md text-sm font-medium transition-colors"
            >
              Create
            </button>
            <button
              onClick={() => setShowCreate(false)}
              className="px-3 py-1.5 bg-surface-hover hover:bg-border text-text rounded-md text-sm transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="border border-border rounded-lg overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-surface-hover text-text-secondary border-b border-border">
            <tr>
              <th className="px-4 py-2.5 font-medium">Name</th>
              <th className="px-4 py-2.5 font-medium">Status</th>
              <th className="px-4 py-2.5 font-medium">URL</th>
              <th className="px-4 py-2.5 font-medium">Command</th>
              <th className="px-4 py-2.5 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {deployments.map((dep) => (
              <tr
                key={dep.id}
                onClick={() => setSelectedId(dep.id)}
                className={`hover:bg-surface-hover transition-colors cursor-pointer ${
                  selectedId === dep.id ? 'bg-surface-hover' : ''
                }`}
              >
                <td className="px-4 py-2.5 text-text font-medium">{dep.name}</td>
                <td className="px-4 py-2.5">
                  <span
                    className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${
                      statusColors[dep.status] || 'text-text-muted bg-text-muted/10'
                    }`}
                  >
                    {dep.status}
                  </span>
                </td>
                <td className="px-4 py-2.5 text-text-secondary">
                  {dep.container_url ? (
                    <a
                      href={dep.container_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-accent hover:underline"
                      onClick={(e) => e.stopPropagation()}
                    >
                      {dep.container_url}
                    </a>
                  ) : (
                    '-'
                  )}
                </td>
                <td className="px-4 py-2.5 text-text-secondary truncate max-w-xs">{dep.command || '-'}</td>
                <td className="px-4 py-2.5 text-right">
                  <div className="flex items-center justify-end gap-1">
                    {dep.status === 'running' ? (
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          stopMutation.mutate(dep.id)
                        }}
                        className="p-1.5 text-text-muted hover:text-warning transition-colors"
                        title="Stop"
                      >
                        <Square size={14} />
                      </button>
                    ) : (
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          startMutation.mutate(dep.id)
                        }}
                        className="p-1.5 text-text-muted hover:text-success transition-colors"
                        title="Start"
                      >
                        <Rocket size={14} />
                      </button>
                    )}
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        setSelectedId(dep.id)
                      }}
                      className="p-1.5 text-text-muted hover:text-accent transition-colors"
                      title="Logs"
                    >
                      <Terminal size={14} />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        deleteMutation.mutate(dep.id)
                      }}
                      className="p-1.5 text-text-muted hover:text-error transition-colors"
                      title="Delete"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {deployments.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-text-muted">
                  No deployments yet
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {selectedId && (
        <div className="bg-surface border border-border rounded-lg p-4 space-y-2">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-medium text-text">Logs</h2>
            <button
              onClick={() => setSelectedId(null)}
              className="text-xs text-text-muted hover:text-text"
            >
              Close
            </button>
          </div>
          <div className="bg-bg border border-border rounded-md p-3 h-64 overflow-auto font-mono text-xs text-text-secondary space-y-0.5">
            {(logsData?.lines || []).map((line: string, i: number) => (
              <div key={i} className="whitespace-pre-wrap">{line || ' '}</div>
            ))}
            {(logsData?.lines || []).length === 0 && (
              <div className="text-text-muted">No logs yet</div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
