export default function EndUserStrategyPage() {
  const sectionStyle = { marginBottom: 36 };
  const h3Style = { color: 'var(--accent)', marginBottom: 12 };
  const cardStyle = { marginBottom: 16, padding: '16px 20px' };
  const dimText = { color: 'var(--text-dim)', fontSize: '0.82rem', lineHeight: 1.7 };
  const labelStyle = { color: 'var(--text)', fontWeight: 700 as const, fontSize: '0.85rem' };
  const tagStyle = (color: string) => ({
    display: 'inline-block', fontSize: '0.65rem', fontWeight: 600 as const,
    padding: '2px 8px', borderRadius: 3, marginLeft: 8,
    background: `${color}22`, color,
  });

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: '32px 24px' }}>
      <h2 style={{ color: 'var(--accent)', marginBottom: 8, borderBottom: '2px solid var(--accent)', paddingBottom: 12 }}>
        Corvus End-User Strategy
      </h2>
      <p style={{ ...dimText, marginBottom: 32 }}>
        Design principles for how Corvus conversations should feel, learn, and evolve &mdash;
        without corrupting the underlying neuron graph.
      </p>

      {/* ── Session Heat: The Core Concept ── */}
      <section style={sectionStyle}>
        <h3 style={h3Style}>Session Heat: Short-Term Potentiation</h3>
        <div className="result-card" style={cardStyle}>
          <p style={dimText}>
            The neuron graph has <strong>long-term plasticity</strong> &mdash; signals like Burst, Impact, and Recency
            change slowly based on actual firings across all users and queries. But within a single conversation,
            users need <strong>short-term potentiation</strong>: a fast-acting, ephemeral amplification that lets them
            drill deep into a topic without permanently warping the graph toward that topic.
          </p>
          <p style={{ ...dimText, marginTop: 12 }}>
            <strong>Biological analogue:</strong> In neuroscience, short-term potentiation (STP) strengthens synaptic
            transmission for seconds to minutes after repeated stimulation. It does not require protein synthesis or
            structural changes &mdash; it&rsquo;s a temporary gain adjustment. Long-term potentiation (LTP) requires
            sustained, patterned activity and produces lasting structural changes. The neuron graph&rsquo;s 6-signal
            scoring is LTP. Session heat is STP.
          </p>
        </div>
      </section>

      {/* ── Tiered Boost Mechanics ── */}
      <section style={sectionStyle}>
        <h3 style={h3Style}>Tiered Continuity Boost</h3>
        <p style={dimText}>
          Each time a neuron fires within a conversation session, its <strong>session heat</strong> increments.
          The backend applies a transient multiplier to the neuron&rsquo;s combined score based on accumulated heat.
          This multiplier never writes back to the graph &mdash; it exists only for the duration of that request.
        </p>
        <div className="result-card" style={cardStyle}>
          <table className="score-table" style={{ fontSize: '0.8rem', width: '100%' }}>
            <thead>
              <tr>
                <th style={{ textAlign: 'left' }}>Session Fires</th>
                <th style={{ textAlign: 'left' }}>Boost</th>
                <th style={{ textAlign: 'left' }}>Effect</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>1</td>
                <td><span style={{ color: '#3b82f6', fontWeight: 600 }}>1.3&times;</span></td>
                <td style={{ color: 'var(--text-dim)' }}>Mild preference &mdash; &ldquo;we talked about this&rdquo;</td>
              </tr>
              <tr>
                <td>2</td>
                <td><span style={{ color: '#8b5cf6', fontWeight: 600 }}>1.6&times;</span></td>
                <td style={{ color: 'var(--text-dim)' }}>Strong pull &mdash; &ldquo;this is clearly the thread&rdquo;</td>
              </tr>
              <tr>
                <td>3+</td>
                <td><span style={{ color: '#ef4444', fontWeight: 600 }}>2.0&times;</span></td>
                <td style={{ color: 'var(--text-dim)' }}>Gravity well &mdash; deep-dive mode, pulls neighbors into top-K</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p style={dimText}>
          At 2.0&times;, neurons that scored 0.4 (normally below top-K threshold) get elevated to 0.8 &mdash;
          competitive with the best-scoring neurons. This is how a user &ldquo;goes 10 layers deep&rdquo; in a session:
          the graph&rsquo;s spread activation reaches further because starting activations are higher, discovering
          second and third-degree neighbors that would never surface in a one-shot query.
        </p>
      </section>

      {/* ── Spread Frontier Seeding ── */}
      <section style={sectionStyle}>
        <h3 style={h3Style}>Elevated Spread Frontier</h3>
        <div className="result-card" style={cardStyle}>
          <p style={dimText}>
            Standard spread activation seeds the frontier with top-K neurons at their combined scores (typically 0.3&ndash;0.8).
            With session heat, high-heat neurons seed at their <em>boosted</em> activation level. A neuron with combined=0.5
            and 3&times; session fires seeds at 1.0 instead of 0.5.
          </p>
          <p style={{ ...dimText, marginTop: 12 }}>
            Higher seed activation means the spread propagation reaches further before falling below the
            <code style={{ background: 'var(--bg-card)', padding: '1px 5px', borderRadius: 3 }}>min_activation</code> threshold.
            With default decay=0.4, a neuron seeded at 1.0 can reach 3 hops (1.0 &rarr; 0.4 &rarr; 0.16 &rarr; 0.064)
            before dropping below 0.05. A neuron seeded at 0.5 only reaches 2 hops (0.5 &rarr; 0.2 &rarr; 0.08).
          </p>
          <p style={{ ...dimText, marginTop: 12, fontStyle: 'italic' }}>
            This is the mechanism that makes &ldquo;10 layers deep&rdquo; possible &mdash; the spread literally reaches
            further because the conversation has built up activation energy.
          </p>
        </div>
      </section>

      {/* ── What Gets Stored vs What Doesn't ── */}
      <section style={sectionStyle}>
        <h3 style={h3Style}>Persistence Boundary</h3>
        <p style={dimText}>
          The critical design constraint: session heat must amplify the user experience without corrupting the graph&rsquo;s
          long-term statistics. Here&rsquo;s exactly what crosses the persistence boundary and what doesn&rsquo;t.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginTop: 16 }}>
          <div className="result-card" style={{ padding: '16px 20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: 12 }}>
              <span style={labelStyle}>Ephemeral (session only)</span>
              <span style={tagStyle('#22c55e')}>NEVER PERSISTED</span>
            </div>
            <ul style={{ ...dimText, paddingLeft: 20, margin: 0 }}>
              <li>Session heat multipliers</li>
              <li>Boosted combined scores</li>
              <li>Elevated spread frontier seeds</li>
              <li>Prompt &ldquo;Conversation Context&rdquo; section</li>
              <li>Frontend neuron accumulator state</li>
            </ul>
            <p style={{ ...dimText, marginTop: 12, fontStyle: 'italic' }}>
              Clear chat = full reset. These live only in the frontend&rsquo;s message array.
            </p>
          </div>

          <div className="result-card" style={{ padding: '16px 20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: 12 }}>
              <span style={labelStyle}>Persisted (graph writes)</span>
              <span style={tagStyle('#ef4444')}>NORMAL PIPELINE</span>
            </div>
            <ul style={{ ...dimText, paddingLeft: 20, margin: 0 }}>
              <li><code>invocations</code> count (unchanged by heat)</li>
              <li><code>avg_utility</code> EMA (only on explicit rating)</li>
              <li>Co-firing edge weights (normal co-fire logic)</li>
              <li>Query record in history table</li>
              <li>Standard burst/recency signal updates</li>
            </ul>
            <p style={{ ...dimText, marginTop: 12, fontStyle: 'italic' }}>
              These follow the normal pipeline. Session heat does not inflate them.
            </p>
          </div>
        </div>
      </section>

      {/* ── Session Traces: The Middle Ground ── */}
      <section style={sectionStyle}>
        <h3 style={h3Style}>Session Traces: Retrospective Learning</h3>
        <div className="result-card" style={cardStyle}>
          <p style={dimText}>
            While session heat never writes to the scoring math in real-time, the <em>patterns</em> of session heat
            are valuable signals that should be captured for retrospective analysis. A <strong>SessionTrace</strong> record
            captures a digest of each conversation when the chat clears or the session ends.
          </p>

          <div style={{ background: 'var(--bg)', borderRadius: 6, padding: '12px 16px', marginTop: 16, fontFamily: 'monospace', fontSize: '0.75rem', color: 'var(--text-dim)', lineHeight: 1.8 }}>
            <div><span style={{ color: '#3b82f6' }}>SessionTrace</span></div>
            <div>&nbsp;&nbsp;neuron_ids: <span style={{ color: '#22c55e' }}>int[]</span> &mdash; ordered list of all neurons that fired</div>
            <div>&nbsp;&nbsp;fire_counts: <span style={{ color: '#22c55e' }}>dict[int, int]</span> &mdash; per-neuron session fire count</div>
            <div>&nbsp;&nbsp;depth: <span style={{ color: '#22c55e' }}>int</span> &mdash; number of conversation turns</div>
            <div>&nbsp;&nbsp;departments_traversed: <span style={{ color: '#22c55e' }}>str[]</span> &mdash; departments touched</div>
            <div>&nbsp;&nbsp;peak_heat_neurons: <span style={{ color: '#22c55e' }}>int[]</span> &mdash; top 5 by session fire count</div>
            <div>&nbsp;&nbsp;timestamp: <span style={{ color: '#22c55e' }}>datetime</span></div>
          </div>
        </div>

        <p style={{ ...dimText, marginTop: 16 }}>
          This is small, append-only, and never touches the scoring engine directly. But it feeds into:
        </p>

        <div className="result-card" style={cardStyle}>
          <div style={{ marginBottom: 16 }}>
            <span style={labelStyle}>1. Autopilot Gap Discovery</span>
            <p style={{ ...dimText, marginTop: 4 }}>
              &ldquo;These neurons keep getting session-boosted to 2.0&times; but have weak base scores (combined &lt; 0.3).
              Maybe their content needs enriching.&rdquo; Session traces reveal neurons the graph is undervaluing &mdash;
              content that users find useful but whose signals haven&rsquo;t caught up yet.
            </p>
          </div>

          <div style={{ marginBottom: 16 }}>
            <span style={labelStyle}>2. Edge Weight Refinement</span>
            <p style={{ ...dimText, marginTop: 4 }}>
              Session co-occurrence is a richer signal than single-query co-firing. Two neurons that fire across
              5 consecutive turns are deeply related even if they never appear in the same single query&rsquo;s top-K.
              Session traces could create or strengthen co-firing edges through a separate, lower-weight pathway.
            </p>
          </div>

          <div style={{ marginBottom: 16 }}>
            <span style={labelStyle}>3. Session Depth as Quality Signal</span>
            <p style={{ ...dimText, marginTop: 4 }}>
              If someone goes 10 turns deep, that conversation was valuable. The neurons involved should probably
              get an impact boost. Currently <code style={{ background: 'var(--bg)', padding: '1px 5px', borderRadius: 3 }}>avg_utility</code> only
              updates on explicit user ratings. Session depth is an implicit quality signal that&rsquo;s currently being left on the table.
            </p>
          </div>

          <div>
            <span style={labelStyle}>4. A 7th Scoring Signal: Session Affinity</span>
            <p style={{ ...dimText, marginTop: 4 }}>
              Neurons that users consistently drill into across multiple sessions have demonstrated value beyond
              what the current 6 signals capture. &ldquo;Session affinity&rdquo; could become a new signal:
              <code style={{ background: 'var(--bg)', padding: '1px 5px', borderRadius: 3 }}>session_affinity = session_fires_total / total_sessions_seen</code>.
              High affinity means &ldquo;when this neuron appears, people want to go deeper.&rdquo;
            </p>
          </div>
        </div>
      </section>

      {/* ── Conversation Context Injection ── */}
      <section style={sectionStyle}>
        <h3 style={h3Style}>Prompt Assembly: Conversation Context</h3>
        <div className="result-card" style={cardStyle}>
          <p style={dimText}>
            Beyond scoring boosts, the assembled system prompt includes a <strong>&ldquo;Conversation Context&rdquo;</strong> section
            that explicitly tells the LLM what knowledge was already surfaced in prior turns. This creates two layers of continuity:
          </p>
          <ol style={{ ...dimText, paddingLeft: 24, marginTop: 12 }}>
            <li style={{ marginBottom: 8 }}>
              <strong>Scoring layer</strong> (implicit): Session heat biases which neurons make it into top-K,
              ensuring related knowledge stays available even when the user&rsquo;s new question has different keywords.
            </li>
            <li>
              <strong>Prompt layer</strong> (explicit): The LLM sees &ldquo;the user has been exploring: [Engineering] FAI Process Design,
              [Quality] Supplier Qualification, [Regulatory] AS9100 Audit Readiness&rdquo; and can connect the dots, building on
              prior answers rather than starting fresh.
            </li>
          </ol>
        </div>
      </section>

      {/* ── Corvus Integration ── */}
      <section style={sectionStyle}>
        <h3 style={h3Style}>Corvus Observation Pipeline Analogue</h3>
        <div className="result-card" style={cardStyle}>
          <p style={dimText}>
            Session traces follow the same pattern as Corvus observations: capture raw signals, queue them for evaluation,
            and only modify the graph after explicit approval. The flow:
          </p>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 16, fontSize: '0.75rem', color: 'var(--text-dim)' }}>
            {['Chat Session', 'Session Trace', 'Pattern Detection', 'Refinement Proposal', 'Human Approval', 'Graph Update'].map((step, i) => (
              <span key={i} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{
                  background: i < 2 ? 'rgba(59,130,246,0.15)' : i < 4 ? 'rgba(139,92,246,0.15)' : 'rgba(34,197,94,0.15)',
                  color: i < 2 ? '#3b82f6' : i < 4 ? '#8b5cf6' : '#22c55e',
                  padding: '4px 10px', borderRadius: 4, fontWeight: 600, whiteSpace: 'nowrap',
                }}>
                  {step}
                </span>
                {i < 5 && <span style={{ color: 'var(--text-dim)' }}>&rarr;</span>}
              </span>
            ))}
          </div>
          <p style={{ ...dimText, marginTop: 16 }}>
            The key constraint: <strong>no automatic graph writes from session data</strong>. Session traces inform
            refinement proposals, which go through the same approval pipeline as Corvus observations.
            A human always decides whether session patterns warrant permanent graph changes.
          </p>
        </div>
      </section>

      {/* ── Implementation Status ── */}
      <section style={sectionStyle}>
        <h3 style={h3Style}>Implementation Status</h3>
        <div className="result-card" style={cardStyle}>
          <table className="score-table" style={{ fontSize: '0.8rem', width: '100%' }}>
            <thead>
              <tr>
                <th style={{ textAlign: 'left' }}>Component</th>
                <th style={{ textAlign: 'left' }}>Status</th>
                <th style={{ textAlign: 'left' }}>Notes</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Prior neuron ID accumulation (frontend)</td>
                <td><span style={tagStyle('#22c55e')}>DONE</span></td>
                <td style={{ color: 'var(--text-dim)' }}>Collects all neuron IDs from prior assistant messages</td>
              </tr>
              <tr>
                <td><code>prior_neuron_ids</code> on QueryRequest</td>
                <td><span style={tagStyle('#22c55e')}>DONE</span></td>
                <td style={{ color: 'var(--text-dim)' }}>Schema field, threaded through executor</td>
              </tr>
              <tr>
                <td>Flat 1.3&times; continuity boost</td>
                <td><span style={tagStyle('#22c55e')}>DONE</span></td>
                <td style={{ color: 'var(--text-dim)' }}>Applied post-scoring, pre-spread</td>
              </tr>
              <tr>
                <td>Conversation Context prompt section</td>
                <td><span style={tagStyle('#22c55e')}>DONE</span></td>
                <td style={{ color: 'var(--text-dim)' }}>Prior neuron labels/summaries injected into assembled prompt</td>
              </tr>
              <tr>
                <td>Tiered boost (1.3&times;/1.6&times;/2.0&times;)</td>
                <td><span style={tagStyle('#f59e0b')}>PLANNED</span></td>
                <td style={{ color: 'var(--text-dim)' }}>Replace flat boost with fire-count-based tiers</td>
              </tr>
              <tr>
                <td>Per-neuron fire count tracking (frontend)</td>
                <td><span style={tagStyle('#f59e0b')}>PLANNED</span></td>
                <td style={{ color: 'var(--text-dim)' }}>Change from <code>number[]</code> to <code>{'{neuron_id, fires}[]'}</code></td>
              </tr>
              <tr>
                <td>Elevated spread frontier seeding</td>
                <td><span style={tagStyle('#f59e0b')}>PLANNED</span></td>
                <td style={{ color: 'var(--text-dim)' }}>High-heat neurons seed spread at boosted activation</td>
              </tr>
              <tr>
                <td>SessionTrace model + storage</td>
                <td><span style={tagStyle('#f59e0b')}>PLANNED</span></td>
                <td style={{ color: 'var(--text-dim)' }}>Append-only digest on chat clear</td>
              </tr>
              <tr>
                <td>Session affinity signal (7th signal)</td>
                <td><span style={tagStyle('#64748b')}>FUTURE</span></td>
                <td style={{ color: 'var(--text-dim)' }}>Requires sufficient session trace data to be meaningful</td>
              </tr>
              <tr>
                <td>Autopilot session pattern mining</td>
                <td><span style={tagStyle('#64748b')}>FUTURE</span></td>
                <td style={{ color: 'var(--text-dim)' }}>Autopilot reads session traces for gap/refinement signals</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* ── Design Principles ── */}
      <section style={sectionStyle}>
        <h3 style={h3Style}>Design Principles</h3>
        <div className="result-card" style={cardStyle}>
          <ol style={{ ...dimText, paddingLeft: 24, margin: 0 }}>
            <li style={{ marginBottom: 12 }}>
              <strong>Session heat is STP, not LTP.</strong> It amplifies within a conversation and vanishes when the chat clears.
              The graph&rsquo;s long-term statistics are never inflated by session dynamics.
            </li>
            <li style={{ marginBottom: 12 }}>
              <strong>Capture patterns, don&rsquo;t execute them.</strong> Session traces are observational data.
              They inform proposals through the same human-in-the-loop pipeline as Corvus observations.
              No automatic graph writes from session data.
            </li>
            <li style={{ marginBottom: 12 }}>
              <strong>Session depth is an implicit quality signal.</strong> A 10-turn conversation is evidence of value
              that doesn&rsquo;t require explicit user ratings. Session traces capture this signal for later use.
            </li>
            <li style={{ marginBottom: 12 }}>
              <strong>New chat = clean slate.</strong> Session state is intentionally non-persistent in the scoring layer.
              A user who wants to explore a different topic simply starts a new conversation and gets an unbiased graph.
            </li>
            <li>
              <strong>The graph should learn from sessions, not during them.</strong> Real-time session heat is for UX.
              Retrospective session analysis is for graph improvement. These are separate systems with separate cadences.
            </li>
          </ol>
        </div>
      </section>
    </div>
  );
}
