import { useRef, useEffect, useCallback } from 'react';
import type { CropRegion, ScreenCaptureState } from '../types/screenCapture';

interface Props {
  capture: ScreenCaptureState;
}

type HandleType = 'nw' | 'n' | 'ne' | 'e' | 'se' | 's' | 'sw' | 'w' | 'move';

interface DragState {
  type: HandleType;
  startX: number;
  startY: number;
  startCrop: CropRegion;
}

const HANDLE_SIZE = 10;
const MIN_CROP = 0.05; // Minimum 5% crop dimension

export default function ScreenPreview({ capture }: Props) {
  const {
    isCapturing, error, stream, framesSent, lastStatus,
    cropRegion, captureInterval,
    startCapture, stopCapture, setCropRegion, setCaptureInterval,
  } = capture;

  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const dragRef = useRef<DragState | null>(null);

  // Attach stream to visible video element
  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream;
    }
  }, [stream]);

  // Drag handlers — follows Explorer.tsx pattern
  useEffect(() => {
    const onMouseMove = (e: MouseEvent) => {
      const drag = dragRef.current;
      const container = containerRef.current;
      if (!drag || !container) return;

      const rect = container.getBoundingClientRect();
      const dx = (e.clientX - drag.startX) / rect.width;
      const dy = (e.clientY - drag.startY) / rect.height;
      const c = drag.startCrop;

      let { left, top, right, bottom } = c;

      if (drag.type === 'move') {
        const w = c.right - c.left;
        const h = c.bottom - c.top;
        left = clamp(c.left + dx, 0, 1 - w);
        top = clamp(c.top + dy, 0, 1 - h);
        right = left + w;
        bottom = top + h;
      } else {
        if (drag.type.includes('w')) left = clamp(c.left + dx, 0, right - MIN_CROP);
        if (drag.type.includes('e')) right = clamp(c.right + dx, left + MIN_CROP, 1);
        if (drag.type.includes('n') && drag.type !== 'ne' && drag.type !== 'nw' || drag.type === 'n')
          top = clamp(c.top + dy, 0, bottom - MIN_CROP);
        if (drag.type.includes('s') && drag.type !== 'se' && drag.type !== 'sw' || drag.type === 's')
          bottom = clamp(c.bottom + dy, top + MIN_CROP, 1);
        // Corner handles move both axes
        if (drag.type === 'nw' || drag.type === 'ne') top = clamp(c.top + dy, 0, bottom - MIN_CROP);
        if (drag.type === 'sw' || drag.type === 'se') bottom = clamp(c.bottom + dy, top + MIN_CROP, 1);
      }

      setCropRegion({ left, top, right, bottom });
    };

    const onMouseUp = () => {
      if (dragRef.current) {
        dragRef.current = null;
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
      }
    };

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };
  }, [setCropRegion]);

  const onHandleDown = useCallback((type: HandleType, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragRef.current = {
      type,
      startX: e.clientX,
      startY: e.clientY,
      startCrop: { ...cropRegion },
    };
    document.body.style.userSelect = 'none';
    document.body.style.cursor = cursorForHandle(type);
  }, [cropRegion]);

  const resetCrop = useCallback(() => {
    setCropRegion({ left: 0, top: 0, right: 1, bottom: 1 });
  }, [setCropRegion]);

  const isFullFrame = cropRegion.left <= 0.01 && cropRegion.top <= 0.01
    && cropRegion.right >= 0.99 && cropRegion.bottom >= 0.99;

  // Not capturing — show start button
  if (!isCapturing) {
    return (
      <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)' }}>
        {error && (
          <div style={{
            marginBottom: 8, padding: '6px 10px', borderRadius: 4,
            background: 'rgba(239,68,68,0.1)', color: '#ef4444', fontSize: '0.7rem',
          }}>
            {error}
          </div>
        )}
        <button
          onClick={startCapture}
          style={{
            width: '100%', padding: '10px 0', borderRadius: 6,
            background: 'var(--accent)', color: '#000', border: 'none',
            cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600,
          }}
        >
          Start Screen Capture
        </button>
        <div style={{ fontSize: '0.65rem', color: 'var(--text-dim)', marginTop: 6, lineHeight: 1.5, textAlign: 'center' }}>
          Your browser will ask which screen, window, or tab to share.
          You control exactly what the advisor can see.
        </div>
      </div>
    );
  }

  // Capturing — show preview with crop overlay
  const l = cropRegion.left * 100;
  const t = cropRegion.top * 100;
  const w = (cropRegion.right - cropRegion.left) * 100;
  const h = (cropRegion.bottom - cropRegion.top) * 100;

  return (
    <div style={{ borderBottom: '1px solid var(--border)' }}>
      {/* Video preview with crop overlay */}
      <div
        ref={containerRef}
        style={{ position: 'relative', margin: '8px 16px', borderRadius: 6, overflow: 'hidden', background: '#000' }}
      >
        <video
          ref={videoRef}
          autoPlay
          muted
          playsInline
          style={{ width: '100%', display: 'block', borderRadius: 6 }}
        />

        {/* Dim overlay outside crop */}
        <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
          {/* Top dim */}
          <div style={{ position: 'absolute', left: 0, top: 0, right: 0, height: `${t}%`, background: 'rgba(0,0,0,0.5)' }} />
          {/* Bottom dim */}
          <div style={{ position: 'absolute', left: 0, bottom: 0, right: 0, height: `${100 - t - h}%`, background: 'rgba(0,0,0,0.5)' }} />
          {/* Left dim */}
          <div style={{ position: 'absolute', left: 0, top: `${t}%`, width: `${l}%`, height: `${h}%`, background: 'rgba(0,0,0,0.5)' }} />
          {/* Right dim */}
          <div style={{ position: 'absolute', right: 0, top: `${t}%`, width: `${100 - l - w}%`, height: `${h}%`, background: 'rgba(0,0,0,0.5)' }} />
        </div>

        {/* Crop rectangle — draggable body */}
        <div
          style={{
            position: 'absolute',
            left: `${l}%`, top: `${t}%`, width: `${w}%`, height: `${h}%`,
            border: '2px solid var(--accent)',
            cursor: 'move',
            boxSizing: 'border-box',
          }}
          onMouseDown={e => onHandleDown('move', e)}
        >
          {/* Corner handles */}
          {(['nw', 'ne', 'sw', 'se'] as HandleType[]).map(handle => (
            <div
              key={handle}
              onMouseDown={e => onHandleDown(handle, e)}
              style={{
                position: 'absolute',
                width: HANDLE_SIZE, height: HANDLE_SIZE,
                background: 'var(--accent)',
                borderRadius: 2,
                cursor: cursorForHandle(handle),
                ...handlePosition(handle),
              }}
            />
          ))}
          {/* Edge handles */}
          {(['n', 'e', 's', 'w'] as HandleType[]).map(handle => (
            <div
              key={handle}
              onMouseDown={e => onHandleDown(handle, e)}
              style={{
                position: 'absolute',
                width: handle === 'n' || handle === 's' ? HANDLE_SIZE * 2 : HANDLE_SIZE / 2,
                height: handle === 'e' || handle === 'w' ? HANDLE_SIZE * 2 : HANDLE_SIZE / 2,
                background: 'var(--accent)',
                borderRadius: 1,
                cursor: cursorForHandle(handle),
                opacity: 0.7,
                ...handlePosition(handle),
              }}
            />
          ))}
        </div>
      </div>

      {/* Controls bar */}
      <div style={{
        padding: '6px 16px 10px', display: 'flex', alignItems: 'center',
        justifyContent: 'space-between', fontSize: '0.65rem', color: 'var(--text-dim)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <button
            onClick={stopCapture}
            style={{
              padding: '3px 10px', borderRadius: 4, fontSize: '0.65rem',
              background: 'rgba(239,68,68,0.15)', color: '#ef4444',
              border: '1px solid rgba(239,68,68,0.3)', cursor: 'pointer',
            }}
          >
            Stop
          </button>
          <span>{framesSent} frames{lastStatus === 'duplicate' ? ' (dup)' : ''}</span>
          {!isFullFrame && (
            <button
              onClick={resetCrop}
              style={{
                padding: '2px 6px', borderRadius: 3, fontSize: '0.6rem',
                background: 'var(--bg-input)', color: 'var(--text-dim)',
                border: '1px solid var(--border)', cursor: 'pointer',
              }}
            >
              Reset Crop
            </button>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <span>Interval:</span>
          <select
            value={captureInterval}
            onChange={e => setCaptureInterval(Number(e.target.value))}
            style={{
              background: 'var(--bg-input)', color: 'var(--text)',
              border: '1px solid var(--border)', borderRadius: 3,
              padding: '1px 4px', fontSize: '0.65rem',
            }}
          >
            {[1, 2, 3, 5, 10].map(s => (
              <option key={s} value={s}>{s}s</option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}


function clamp(val: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, val));
}

function cursorForHandle(type: HandleType): string {
  const map: Record<HandleType, string> = {
    nw: 'nwse-resize', ne: 'nesw-resize', sw: 'nesw-resize', se: 'nwse-resize',
    n: 'ns-resize', s: 'ns-resize', e: 'ew-resize', w: 'ew-resize',
    move: 'move',
  };
  return map[type];
}

function handlePosition(type: HandleType): React.CSSProperties {
  const offset = -(HANDLE_SIZE / 2);
  switch (type) {
    case 'nw': return { left: offset, top: offset };
    case 'ne': return { right: offset, top: offset };
    case 'sw': return { left: offset, bottom: offset };
    case 'se': return { right: offset, bottom: offset };
    case 'n': return { left: '50%', top: offset, transform: 'translateX(-50%)' };
    case 's': return { left: '50%', bottom: offset, transform: 'translateX(-50%)' };
    case 'e': return { right: offset, top: '50%', transform: 'translateY(-50%)' };
    case 'w': return { left: offset, top: '50%', transform: 'translateY(-50%)' };
    default: return {};
  }
}
