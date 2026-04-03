export interface CropRegion {
  left: number;   // 0.0–1.0 percentage from left edge
  top: number;    // 0.0–1.0 percentage from top edge
  right: number;  // 0.0–1.0 percentage from right edge
  bottom: number; // 0.0–1.0 percentage from bottom edge
}

export interface ScreenCaptureState {
  isCapturing: boolean;
  error: string | null;
  framesSent: number;
  lastStatus: string | null;
  cropRegion: CropRegion;
  captureInterval: number;
  stream: MediaStream | null;
  startCapture: () => Promise<void>;
  stopCapture: () => void;
  setCropRegion: (region: CropRegion) => void;
  setCaptureInterval: (seconds: number) => void;
}
