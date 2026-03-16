import { useCallback, useEffect, useRef, useState } from 'react';
import {
  sendChat, submitQueryStream, createSession, listSessions, getSession,
  appendMessage, generateSessionTitle, deleteSession,
  type ChatMessage, type ChatResponse, type StageEvent, type SlotSpec,
  type SessionSummary,
} from '../api';
import type { NeuronScoreResponse } from '../types';
import ChatPipeline from './ChatPipeline';
import ConversationGraph from './ConversationGraph';

/** Lightweight inline markdown: **bold**, *italic*, bullet lists, and paragraphs. */
function renderMarkdown(text: string) {
  const paragraphs = text.split(/\n{2,}/);
  return paragraphs.map((para, pi) => {
    const trimmed = para.trim();
    const lines = trimmed.split('\n');
    const isList = lines.every(l => /^[-*•]\s/.test(l.trim()));
    if (isList) {
      return (
        <ul key={pi} style={{ margin: '0.3em 0', paddingLeft: '1.2em' }}>
          {lines.map((l, li) => (
            <li key={li}>{inlineFormat(l.replace(/^[-*•]\s/, ''))}</li>
          ))}
        </ul>
      );
    }
    return <p key={pi} style={{ margin: '0.3em 0' }}>{inlineFormat(trimmed)}</p>;
  });
}

function inlineFormat(text: string) {
  const parts: (string | React.ReactElement)[] = [];
  const re = /(\*\*(.+?)\*\*|\*(.+?)\*)/g;
  let match: RegExpExecArray | null;
  let lastIndex = 0;
  let key = 0;
  while ((match = re.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    if (match[2]) {
      parts.push(<strong key={key++}>{match[2]}</strong>);
    } else if (match[3]) {
      parts.push(<em key={key++}>{match[3]}</em>);
    }
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }
  return <>{parts}</>;
}

interface Message {
  role: 'user' | 'assistant';
  text: string;
  model?: string;
  tokens?: { input: number; output: number };
  cost?: number;
  neurons_activated?: number;
  neuron_scores?: NeuronScoreResponse[];
}

function relativeTime(iso: string): string {
  const d = new Date(iso);
  const now = Date.now();
  const diffMs = now - d.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return 'just now';
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDay = Math.floor(diffHr / 24);
  if (diffDay === 1) return 'Yesterday';
  if (diffDay < 7) return `${diffDay}d ago`;
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

export default function HomePage({ onNavigate }: { onNavigate: (tab: string) => void }) {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [model, setModel] = useState<'haiku' | 'sonnet' | 'opus'>('haiku');
  const [useNeurons, setUseNeurons] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Session persistence
  const [currentSessionId, setCurrentSessionId] = useState<number | null>(null);
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(true);
  const sessionCreatingRef = useRef(false);

  // Live pipeline state for streaming neuron queries
  const [pipelineStages, setPipelineStages] = useState<Record<string, StageEvent>>({});
  const [pipelineDone, setPipelineDone] = useState(false);

  // Load sessions on mount
  useEffect(() => {
    listSessions().then(setSessions).catch(() => {}).finally(() => setSessionsLoading(false));
  }, []);

  const refreshSessions = useCallback(() => {
    listSessions().then(setSessions).catch(() => {});
  }, []);

  // Auto-scroll as pipeline stages update
  useEffect(() => {
    if (loading) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [pipelineStages, loading]);

  async function handleSend() {
    const text = input.trim();
    if (!text || loading) return;
    setInput('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
    const userMsg: Message = { role: 'user', text };
    const isFirstMessage = messages.length === 0;
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);
    setPipelineStages({});
    setPipelineDone(false);

    try {
      // Ensure we have a session
      let sessionId = currentSessionId;
      if (sessionId === null && !sessionCreatingRef.current) {
        sessionCreatingRef.current = true;
        try {
          const s = await createSession();
          sessionId = s.id;
          setCurrentSessionId(s.id);
        } finally {
          sessionCreatingRef.current = false;
        }
      }

      // Persist user message (await to ensure it's saved before LLM call)
      if (sessionId) {
        await appendMessage(sessionId, { role: 'user', text });
      }

      let assistantMsg: Message;
      if (useNeurons) {
        // Use streaming endpoint for live pipeline feedback
        // Build conversation context so the LLM sees prior messages
        const recentHistory = messages.slice(-10);
        let userMessage = text;
        if (recentHistory.length > 0) {
          const historyLines = recentHistory.map(m =>
            `${m.role === 'user' ? 'User' : 'Assistant'}: ${m.text.slice(0, 500)}`
          ).join('\n');
          userMessage = `[Conversation so far]\n${historyLines}\n\nUser: ${text}`;
        }
        // Collect neuron IDs from all prior assistant messages for continuity
        const priorNeuronIds: number[] = [];
        for (const m of messages) {
          if (m.neuron_scores) {
            for (const ns of m.neuron_scores) {
              priorNeuronIds.push(ns.neuron_id);
            }
          }
        }

        const slot: SlotSpec = { mode: `${model}_neuron`, token_budget: 2048, top_k: 12 };
        const { promise } = submitQueryStream(
          userMessage,
          [slot],
          (event: StageEvent) => {
            setPipelineStages(prev => ({ ...prev, [event.stage]: event }));
          },
          'conversational',
          priorNeuronIds.length > 0 ? priorNeuronIds : undefined,
        );
        const res = await promise;
        setPipelineDone(true);
        const slotResult = res.slots[0];
        assistantMsg = {
          role: 'assistant',
          text: slotResult?.response ?? '',
          model,
          tokens: {
            input: (res.classify_input_tokens || 0) + (slotResult?.input_tokens || 0),
            output: (res.classify_output_tokens || 0) + (slotResult?.output_tokens || 0),
          },
          cost: res.total_cost || 0,
          neurons_activated: res.neurons_activated,
          neuron_scores: res.neuron_scores,
        };
      } else {
        const history: ChatMessage[] = messages.map(m => ({ role: m.role, text: m.text }));
        const res: ChatResponse = await sendChat(text, model, history);
        assistantMsg = {
          role: 'assistant',
          text: res.response,
          model: res.model,
          tokens: { input: res.input_tokens, output: res.output_tokens },
          cost: res.cost_usd,
        };
      }
      setMessages(prev => [...prev, assistantMsg]);

      // Persist assistant message (await so it's saved before title generation)
      if (sessionId) {
        await appendMessage(sessionId, {
          role: 'assistant',
          text: assistantMsg.text,
          model: assistantMsg.model,
          input_tokens: assistantMsg.tokens?.input,
          output_tokens: assistantMsg.tokens?.output,
          cost: assistantMsg.cost,
          neurons_activated: assistantMsg.neurons_activated,
          neuron_scores: assistantMsg.neuron_scores,
        });
      }

      // Auto-generate title after first exchange (messages are now persisted)
      if (isFirstMessage && sessionId) {
        generateSessionTitle(sessionId).then(() => refreshSessions()).catch(() => {});
      }
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', text: `Error: ${e instanceof Error ? e.message : 'Failed'}` }]);
    } finally {
      setLoading(false);
      setPipelineStages({});
      setPipelineDone(false);
      setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);
    }
  }

  function startNewChat() {
    setCurrentSessionId(null);
    setMessages([]);
    refreshSessions();
  }

  async function loadSession(id: number) {
    try {
      const detail = await getSession(id);
      setCurrentSessionId(id);
      setMessages(detail.messages.map(m => ({
        role: m.role as 'user' | 'assistant',
        text: m.text,
        model: m.model ?? undefined,
        tokens: (m.input_tokens || m.output_tokens) ? { input: m.input_tokens, output: m.output_tokens } : undefined,
        cost: m.cost || undefined,
        neurons_activated: m.neurons_activated || undefined,
        neuron_scores: m.neuron_scores ?? undefined,
      })));
    } catch {
      // Session may have been deleted
    }
  }

  async function archiveSession(id: number) {
    await deleteSession(id).catch(() => {});
    setSessions(prev => prev.filter(s => s.id !== id));
    if (currentSessionId === id) {
      startNewChat();
    }
  }

  const hasMessages = messages.length > 0 || currentSessionId !== null;

  // Find the most recent assistant message with neuron scores for the sidebar
  let latestNeuronMsg: Message | null = null;
  for (let i = messages.length - 1; i >= 0; i--) {
    if (messages[i].role === 'assistant' && messages[i].neuron_scores && messages[i].neuron_scores!.length > 0) {
      latestNeuronMsg = messages[i];
      break;
    }
  }

  const showSidebar = hasMessages && useNeurons && (latestNeuronMsg || loading);

  return (
    <div className={`home-page${showSidebar ? ' home-page--with-sidebar' : ''}`}>
      {!hasMessages && (
        <div className="home-hero">
          <img src="/corvus-logo.png" alt="Corvus" className="home-logo" />
          <h1 className="home-title">Corvus</h1>
          <p className="home-subtitle">Biomimetic knowledge graph for organizational intelligence</p>
          <div className="home-shortcuts">
            <button className="home-shortcut" onClick={() => onNavigate('query')}>
              <svg className="home-shortcut-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
              </svg>
              <span>Query Lab</span>
            </button>
            <button className="home-shortcut" onClick={() => onNavigate('explorer')}>
              <svg className="home-shortcut-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="3" />
                <circle cx="12" cy="12" r="9" />
                <line x1="12" y1="3" x2="12" y2="6" />
                <line x1="12" y1="18" x2="12" y2="21" />
                <line x1="3" y1="12" x2="6" y2="12" />
                <line x1="18" y1="12" x2="21" y2="12" />
              </svg>
              <span>Explorer</span>
            </button>
            <button className="home-shortcut" onClick={() => onNavigate('corvus-observations')}>
              <svg className="home-shortcut-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="7" />
                <line x1="16.5" y1="16.5" x2="21" y2="21" />
              </svg>
              <span>Observations</span>
            </button>
            <button className="home-shortcut" onClick={() => onNavigate('dashboard')}>
              <svg className="home-shortcut-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="4 18 8 10 12 14 16 6 20 12" />
                <line x1="4" y1="20" x2="20" y2="20" />
              </svg>
              <span>Dashboard</span>
            </button>
          </div>
          {!sessionsLoading && sessions.length > 0 && (
            <div className="home-recent-sessions">
              <h3>Recent Conversations</h3>
              {sessions.slice(0, 10).map(s => (
                <div key={s.id} className="home-session-card" onClick={() => loadSession(s.id)}>
                  <span className="home-session-title">{s.title || 'Untitled'}</span>
                  <span className="home-session-time">{relativeTime(s.updated_at)}</span>
                  <button className="home-session-delete" onClick={e => { e.stopPropagation(); archiveSession(s.id); }}>×</button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {hasMessages && (
        <div className="home-chat-center">
          <div className="home-chat-messages">
            {messages.map((msg, i) => (
              <div key={i} className={`home-chat-msg home-chat-msg--${msg.role}`}>
                <div className="home-chat-bubble">
                  <div className="home-chat-text">{msg.role === 'assistant' ? renderMarkdown(msg.text) : msg.text}</div>
                  {msg.role === 'assistant' && msg.model && (
                    <div className="home-chat-meta">
                      <span>{msg.model}{msg.neurons_activated != null ? ' + neurons' : ''}</span>
                      {msg.neurons_activated != null ? <span>{msg.neurons_activated} neurons</span> : null}
                      {msg.tokens ? <span>{msg.tokens.input + msg.tokens.output} tokens</span> : null}
                      {msg.cost != null ? <span>${msg.cost.toFixed(4)}</span> : null}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="home-chat-msg home-chat-msg--assistant">
                <div className="home-chat-bubble">
                  {useNeurons && Object.keys(pipelineStages).length > 0 ? (
                    <ChatPipeline stages={pipelineStages} done={pipelineDone} />
                  ) : (
                    <span className="home-chat-typing">Thinking...</span>
                  )}
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className={`home-input-area home-input-area--bottom`}>
            <div className="home-input-controls">
              <button className="home-new-chat-btn" onClick={startNewChat} title="Start a new conversation">
                + New Chat
              </button>
              <select
                className="home-model-select"
                value={model}
                onChange={e => setModel(e.target.value as 'haiku' | 'sonnet' | 'opus')}
              >
                <option value="haiku">Haiku</option>
                <option value="sonnet">Sonnet</option>
                <option value="opus">Opus</option>
              </select>
              <button
                className={`home-neuron-pill${useNeurons ? ' home-neuron-pill--active' : ''}`}
                onClick={() => setUseNeurons(v => !v)}
                title="Toggle neuron-enriched context from the knowledge graph"
              >
                <svg className="home-neuron-pill-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <circle cx="8" cy="8" r="3" />
                  <line x1="8" y1="1" x2="8" y2="4" />
                  <line x1="8" y1="12" x2="8" y2="15" />
                  <line x1="1" y1="8" x2="4" y2="8" />
                  <line x1="12" y1="8" x2="15" y2="8" />
                  <line x1="3.5" y1="3.5" x2="5.5" y2="5.5" />
                  <line x1="10.5" y1="10.5" x2="12.5" y2="12.5" />
                  <line x1="3.5" y1="12.5" x2="5.5" y2="10.5" />
                  <line x1="10.5" y1="5.5" x2="12.5" y2="3.5" />
                </svg>
                Neurons
              </button>
            </div>
            <div className="home-input-row">
              <textarea
                ref={textareaRef}
                className="home-input"
                placeholder="Ask anything..."
                value={input}
                onChange={e => {
                  setInput(e.target.value);
                  e.target.style.height = 'auto';
                  e.target.style.height = e.target.scrollHeight + 'px';
                }}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
                rows={1}
              />
              <button className="home-send-btn" onClick={handleSend} disabled={loading || !input.trim()}>
                &#10148;
              </button>
            </div>
          </div>
        </div>
      )}

      {!hasMessages && (
        <div className="home-input-area">
          <div className="home-input-controls">
            <select
              className="home-model-select"
              value={model}
              onChange={e => setModel(e.target.value as 'haiku' | 'sonnet' | 'opus')}
            >
              <option value="haiku">Haiku</option>
              <option value="sonnet">Sonnet</option>
              <option value="opus">Opus</option>
            </select>
            <button
              className={`home-neuron-pill${useNeurons ? ' home-neuron-pill--active' : ''}`}
              onClick={() => setUseNeurons(v => !v)}
              title="Toggle neuron-enriched context from the knowledge graph"
            >
              <svg className="home-neuron-pill-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
                <circle cx="8" cy="8" r="3" />
                <line x1="8" y1="1" x2="8" y2="4" />
                <line x1="8" y1="12" x2="8" y2="15" />
                <line x1="1" y1="8" x2="4" y2="8" />
                <line x1="12" y1="8" x2="15" y2="8" />
                <line x1="3.5" y1="3.5" x2="5.5" y2="5.5" />
                <line x1="10.5" y1="10.5" x2="12.5" y2="12.5" />
                <line x1="3.5" y1="12.5" x2="5.5" y2="10.5" />
                <line x1="10.5" y1="5.5" x2="12.5" y2="3.5" />
              </svg>
              Neurons
            </button>
          </div>
          <div className="home-input-row">
            <textarea
              ref={textareaRef}
              className="home-input"
              placeholder="Ask anything..."
              value={input}
              onChange={e => {
                setInput(e.target.value);
                e.target.style.height = 'auto';
                e.target.style.height = e.target.scrollHeight + 'px';
              }}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
              rows={1}
            />
            <button className="home-send-btn" onClick={handleSend} disabled={loading || !input.trim()}>
              &#10148;
            </button>
          </div>
        </div>
      )}

      {showSidebar && (
        <div className="home-neuron-sidebar">
          {latestNeuronMsg ? (
            <ConversationGraph
              messages={messages}
              onNavigateToNeuron={(id) => onNavigate(`neuron/${id}`)}
            />
          ) : loading && useNeurons ? (
            <div className="home-neuron-sidebar-loading">
              <span className="home-chat-typing">Building neuron tree...</span>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}
