import { useState, useRef, useCallback, useEffect } from 'react'
import { submitQueryStream } from '../api'
import type { QueryResponse, StageEvent } from '../types'
import NeuronTreeViz from './NeuronTreeViz'
import { marked } from 'marked'

marked.setOptions({ breaks: true, gfm: true });

export default function NeuronConfidencePage() {
  const [message, setMessage] = useState('')
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.5)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<QueryResponse | null>(null)
  const [elapsedMs, setElapsedMs] = useState(0)
  const elapsedRef = useRef(0)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const abortRef = useRef<(() => void) | null>(null)

  async function handleSubmit() {
    if (!message.trim()) return
    if (abortRef.current) { abortRef.current(); abortRef.current = null; }

    setLoading(true)
    setError('')
    setResult(null)

    const t0 = Date.now()
    elapsedRef.current = 0
    setElapsedMs(0)
    if (timerRef.current) clearInterval(timerRef.current)
    timerRef.current = setInterval(() => {
      elapsedRef.current = Date.now() - t0
      setElapsedMs(elapsedRef.current)
    }, 100)

    try {
      const { promise, abort } = submitQueryStream(
        message,
        true, // agent_mode
        confidenceThreshold,
        (_event: StageEvent) => {
          // Just track stages, no need to display them here
        }
      )
      abortRef.current = abort
      const res = await promise
      setResult(res)
    } catch (e) {
      if ((e as Error).name !== 'AbortError') {
        setError(e instanceof Error ? e.message : 'Query failed')
      }
    } finally {
      abortRef.current = null
      if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
      setElapsedMs(elapsedRef.current)
      setLoading(false)
    }
  }

  return (
    <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '16px', height: '100%' }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <h2 style={{ margin: 0, fontSize: '1.4rem' }}>Neuron Confidence Threshold Testing</h2>
        <p style={{ margin: 0, color: 'var(--text-dim)', fontSize: '0.9rem' }}>
          Test how different confidence thresholds filter the neuron activation graph. Adjust the slider to see which neurons are selected for each query.
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', borderRadius: '6px', padding: '12px', background: 'var(--bg-secondary)' }}>
        <div>
          <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem', fontWeight: 500 }}>
            Query Message
          </label>
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Enter a query to test confidence filtering..."
            style={{
              width: '100%',
              minHeight: '80px',
              padding: '8px',
              borderRadius: '4px',
              border: '1px solid var(--border)',
              background: 'var(--bg)',
              color: 'var(--text)',
              fontFamily: 'inherit',
              fontSize: '0.9rem',
            }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <label style={{ whiteSpace: 'nowrap', fontSize: '0.9rem', fontWeight: 500 }}>
            Confidence Threshold (θ): <span style={{ fontSize: '1rem', fontFamily: 'monospace', color: 'var(--accent)' }}>{confidenceThreshold.toFixed(2)}</span>
          </label>
          <input
            type="range"
            min="0.1"
            max="1.0"
            step="0.05"
            value={confidenceThreshold}
            onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
            style={{ flex: 1, minWidth: '150px', cursor: 'pointer' }}
          />
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <button
            onClick={handleSubmit}
            disabled={loading || !message.trim()}
            style={{
              padding: '8px 16px',
              borderRadius: '4px',
              border: 'none',
              background: 'var(--accent)',
              color: 'white',
              cursor: loading || !message.trim() ? 'not-allowed' : 'pointer',
              opacity: loading || !message.trim() ? 0.5 : 1,
              fontSize: '0.9rem',
              fontWeight: 500,
            }}
          >
            {loading ? `Processing (${(elapsedMs / 1000).toFixed(1)}s)` : 'Submit'}
          </button>
        </div>

        {error && (
          <div style={{
            padding: '8px 12px',
            borderRadius: '4px',
            background: '#ef444422',
            border: '1px solid #ef444444',
            color: '#fca5a5',
            fontSize: '0.85rem',
          }}>
            {error}
          </div>
        )}
      </div>

      {result && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', flex: 1 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ margin: 0, fontSize: '1.1rem' }}>Neuron Activation Graph</h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-dim)' }}>
              {result.neurons_activated} neurons activated • {(elapsedMs / 1000).toFixed(1)}s
            </span>
          </div>

          {result.neuron_scores.length > 0 ? (
            <div style={{ height: '400px', flex: 1, minHeight: '400px' }}>
              <NeuronTreeViz
                queryId={result.query_id}
                neuronScores={result.neuron_scores}
                agentResults={result.agent_execution?.agent_results}
              />
            </div>
          ) : (
            <div style={{
              padding: '32px',
              textAlign: 'center',
              borderRadius: '6px',
              background: 'var(--bg-secondary)',
              color: 'var(--text-dim)',
            }}>
              No neurons activated for this query
            </div>
          )}

          {result.agent_execution && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '16px' }}>
              <h3 style={{ margin: 0, fontSize: '1.1rem' }}>Agent Results</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '12px' }}>
                {result.agent_execution.agent_results.map((agent) => (
                  <div
                    key={`${agent.domain_key}-${agent.role_key}`}
                    style={{
                      padding: '12px',
                      borderRadius: '6px',
                      border: '1px solid var(--border)',
                      background: 'var(--bg-secondary)',
                    }}
                  >
                    <div style={{ fontWeight: 600, marginBottom: '6px' }}>
                      {agent.role} <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>({agent.domain_key})</span>
                    </div>
                    {agent.flags.length > 0 && (
                      <div style={{ display: 'flex', gap: '6px', marginBottom: '8px', flexWrap: 'wrap' }}>
                        {agent.flags.map((flag) => (
                          <span
                            key={flag}
                            style={{
                              fontSize: '0.7rem',
                              padding: '2px 6px',
                              borderRadius: '3px',
                              background: flag.includes('CRITICAL') ? '#ef444422' : '#fb923c22',
                              color: flag.includes('CRITICAL') ? '#ef4444' : '#fb923c',
                              fontWeight: 600,
                            }}
                          >
                            {flag}
                          </span>
                        ))}
                      </div>
                    )}
                    <div style={{
                      fontSize: '0.85rem',
                      lineHeight: '1.4',
                      maxHeight: '150px',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                    }}>
                      {agent.findings}
                    </div>
                    <div style={{ fontSize: '0.75rem', marginTop: '8px', color: 'var(--text-dim)' }}>
                      Confidence: {(agent.confidence * 100).toFixed(0)}%
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {result.agent_execution?.synthesis && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '16px' }}>
              <h3 style={{ margin: 0, fontSize: '1.1rem' }}>Synthesis</h3>
              <div
                className="markdown-body"
                style={{
                  padding: '12px',
                  borderRadius: '6px',
                  background: 'var(--bg-secondary)',
                  border: '1px solid var(--border)',
                }}
                dangerouslySetInnerHTML={{ __html: marked.parse(result.agent_execution.synthesis, { async: false }) as string }}
              />
            </div>
          )}
        </div>
      )}
    </div>
  )
}
