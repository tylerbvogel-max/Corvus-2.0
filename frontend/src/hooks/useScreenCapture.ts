import { useState, useRef, useCallback, useEffect } from 'react';
import type { CropRegion, ScreenCaptureState } from '../types/screenCapture';

const CORVUS_API = '/corvus';
const DEFAULT_INTERVAL = 3;
const DEFAULT_CROP: CropRegion = { left: 0, top: 0, right: 1, bottom: 1 };
const JPEG_QUALITY = 0.6;

export default function useScreenCapture(): ScreenCaptureState {
  const [isCapturing, setIsCapturing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [framesSent, setFramesSent] = useState(0);
  const [lastStatus, setLastStatus] = useState<string | null>(null);
  const [cropRegion, setCropRegionState] = useState<CropRegion>(DEFAULT_CROP);
  const [captureInterval, setCaptureIntervalState] = useState(DEFAULT_INTERVAL);
  const [stream, setStream] = useState<MediaStream | null>(null);

  // Refs for values accessed inside setInterval closure
  const streamRef = useRef<MediaStream | null>(null);
  const cropRef = useRef<CropRegion>(DEFAULT_CROP);
  const intervalRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const cropCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const intervalSecsRef = useRef(DEFAULT_INTERVAL);

  // Keep refs in sync with state
  const setCropRegion = useCallback((region: CropRegion) => {
    setCropRegionState(region);
    cropRef.current = region;
  }, []);

  const setCaptureInterval = useCallback((seconds: number) => {
    setCaptureIntervalState(seconds);
    intervalSecsRef.current = seconds;
    // Restart interval if capturing
    if (intervalRef.current && streamRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = setInterval(captureAndPost, seconds * 1000);
    }
  }, []);

  const captureAndPost = useCallback(async () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const cropCanvas = cropCanvasRef.current;
    if (!video || !canvas || !cropCanvas || video.readyState < 2) return;

    const vw = video.videoWidth;
    const vh = video.videoHeight;
    if (vw === 0 || vh === 0) return;

    // Draw full frame to main canvas
    canvas.width = vw;
    canvas.height = vh;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.drawImage(video, 0, 0, vw, vh);

    // Compute crop pixels
    const crop = cropRef.current;
    const cx = Math.round(crop.left * vw);
    const cy = Math.round(crop.top * vh);
    const cw = Math.round((crop.right - crop.left) * vw);
    const ch = Math.round((crop.bottom - crop.top) * vh);
    if (cw <= 0 || ch <= 0) return;

    // Draw cropped region to crop canvas
    cropCanvas.width = cw;
    cropCanvas.height = ch;
    const cropCtx = cropCanvas.getContext('2d');
    if (!cropCtx) return;
    cropCtx.drawImage(canvas, cx, cy, cw, ch, 0, 0, cw, ch);

    // Convert to JPEG blob and POST
    cropCanvas.toBlob(async (blob) => {
      if (!blob) return;
      const fd = new FormData();
      fd.append('frame', blob, 'frame.jpg');
      fd.append('timestamp', new Date().toISOString());
      fd.append('width', String(cw));
      fd.append('height', String(ch));

      try {
        const r = await fetch(`${CORVUS_API}/capture`, { method: 'POST', body: fd });
        if (r.ok) {
          const data = await r.json();
          setLastStatus(data.status ?? 'ok');
          setFramesSent(prev => prev + 1);
        }
      } catch {
        // Backend unreachable — don't crash the loop
      }
    }, 'image/jpeg', JPEG_QUALITY);
  }, []);

  const startCapture = useCallback(async () => {
    setError(null);
    try {
      const mediaStream = await navigator.mediaDevices.getDisplayMedia({
        video: { cursor: 'always' } as MediaTrackConstraints,
      });

      // Create hidden video element for frame extraction
      const video = document.createElement('video');
      video.srcObject = mediaStream;
      video.muted = true;
      video.playsInline = true;
      await video.play();

      // Create hidden canvases
      const canvas = document.createElement('canvas');
      const cropCanvas = document.createElement('canvas');

      // Store refs
      videoRef.current = video;
      canvasRef.current = canvas;
      cropCanvasRef.current = cropCanvas;
      streamRef.current = mediaStream;
      setStream(mediaStream);
      setIsCapturing(true);
      setFramesSent(0);
      setLastStatus(null);

      // Handle user clicking browser's "Stop sharing" button
      mediaStream.getVideoTracks()[0].onended = () => {
        stopCaptureInternal();
      };

      // Start frame capture loop
      intervalRef.current = setInterval(captureAndPost, intervalSecsRef.current * 1000);

      // Capture first frame immediately after a short delay for video to initialize
      setTimeout(captureAndPost, 500);

    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Screen capture failed';
      if (msg.includes('Permission denied') || msg.includes('NotAllowedError')) {
        setError('Screen capture was cancelled.');
      } else {
        setError(msg);
      }
    }
  }, [captureAndPost]);

  const stopCaptureInternal = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = undefined;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
      videoRef.current = null;
    }
    canvasRef.current = null;
    cropCanvasRef.current = null;
    setStream(null);
    setIsCapturing(false);
  }, []);

  const stopCapture = useCallback(() => {
    stopCaptureInternal();
  }, [stopCaptureInternal]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop());
    };
  }, []);

  return {
    isCapturing,
    error,
    framesSent,
    lastStatus,
    cropRegion,
    captureInterval,
    stream,
    startCapture,
    stopCapture,
    setCropRegion,
    setCaptureInterval,
  };
}
