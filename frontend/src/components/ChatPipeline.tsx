import { useEffect, useState } from 'react';
import type { StageEvent } from '../api';

/**
 * Compact inline pipeline tracker for the chat UI.
 * Shows neuron pipeline stages progressing in real time.
 */

const STAGES: { key: string; label: string }[] = [
  { key: 'input_guard', label: 'Guard' },
  { key: 'structural_resolve', label: 'Resolve' },
  { key: 'classify', label: 'Classify' },
  { key: 'score_neurons', label: 'Score' },
  { key: 'spread_activation', label: 'Spread' },
  { key: 'assemble_prompt', label: 'Assemble' },
  { key: 'execute_llm', label: 'Execute' },
];

interface Props {
  stages: Record<string, StageEvent>;
  done: boolean;
}

export default function ChatPipeline({ stages, done }: Props) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (done) return;
    const t0 = Date.now();
    const id = setInterval(() => setElapsed(Date.now() - t0), 100);
    return () => clearInterval(id);
  }, [done]);

  // Find the last stage that has received an event
  let activeIdx = -1;
  for (let i = STAGES.length - 1; i >= 0; i--) {
    if (stages[STAGES[i].key]) { activeIdx = i; break; }
  }

  return (
    <div className="chat-pipeline">
      <div className="chat-pipeline-stages">
        {STAGES.map((stage, i) => {
          const ev = stages[stage.key];
          const isDone = !!ev && (ev.status === 'done' || ev.status === 'skipped');
          const isCurrentlyActive = !done && i === activeIdx && !stages[STAGES[i + 1]?.key];
          const isWaiting = !ev;

          return (
            <div
              key={stage.key}
              className={`chat-pipeline-step${isDone ? ' chat-pipeline-step--done' : ''}${isCurrentlyActive ? ' chat-pipeline-step--active' : ''}${isWaiting ? ' chat-pipeline-step--waiting' : ''}`}
            >
              <span className="chat-pipeline-dot" />
              <span className="chat-pipeline-label">{stage.label}</span>
              {ev?.detail && stage.key === 'classify' && ev.detail.intent ? (
                <span className="chat-pipeline-detail">{String(ev.detail.intent).replace(/_/g, ' ')}</span>
              ) : null}
              {ev?.detail && stage.key === 'score_neurons' && ev.detail.scored ? (
                <span className="chat-pipeline-detail">{String(ev.detail.scored)} neurons</span>
              ) : null}
              {ev?.detail && stage.key === 'assemble_prompt' && ev.detail.neurons_activated ? (
                <span className="chat-pipeline-detail">{String(ev.detail.neurons_activated)} activated</span>
              ) : null}
            </div>
          );
        })}
      </div>
      {!done && (
        <div className="chat-pipeline-timer">{(elapsed / 1000).toFixed(1)}s</div>
      )}
    </div>
  );
}
