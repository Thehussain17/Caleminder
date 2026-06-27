// Web Audio API — layered tactile sounds for an immensely satisfying UI
const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

function resumeCtx() {
  if (audioCtx.state === 'suspended') audioCtx.resume();
}

// Shared helper: create an oscillator and gain, connect and schedule it
function scheduleOsc(type, freq, freqTarget, gainStart, gainEnd, start, duration) {
  const osc = audioCtx.createOscillator();
  const gain = audioCtx.createGain();
  osc.type = type;
  osc.frequency.setValueAtTime(freq, start);
  if (freqTarget) osc.frequency.exponentialRampToValueAtTime(freqTarget, start + duration);
  gain.gain.setValueAtTime(gainStart, start);
  gain.gain.exponentialRampToValueAtTime(0.0001, start + duration);
  osc.connect(gain);
  gain.connect(audioCtx.destination);
  osc.start(start);
  osc.stop(start + duration + 0.01);
}

// Noise burst helper for the "click" transient
function scheduleNoise(gainStart, start, duration) {
  const bufferSize = Math.floor(audioCtx.sampleRate * duration);
  const buffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
  const data = buffer.getChannelData(0);
  for (let i = 0; i < bufferSize; i++) data[i] = Math.random() * 2 - 1;
  const source = audioCtx.createBufferSource();
  source.buffer = buffer;
  const gain = audioCtx.createGain();
  // High-pass filter to make it clicky not boomy
  const filter = audioCtx.createBiquadFilter();
  filter.type = 'highpass';
  filter.frequency.value = 2000;
  gain.gain.setValueAtTime(gainStart, start);
  gain.gain.exponentialRampToValueAtTime(0.0001, start + duration);
  source.connect(filter);
  filter.connect(gain);
  gain.connect(audioCtx.destination);
  source.start(start);
  source.stop(start + duration + 0.01);
}

// ─── Click Sound ────────────────────────────────────────────────────────────
// A satisfying tri-layer click: noise transient + square blip + sine sub-thump
export function playClickSound() {
  resumeCtx();
  const t = audioCtx.currentTime;
  scheduleNoise(0.18, t, 0.025);                           // crisp transient
  scheduleOsc('square', 520, 160, 0.06, 0.0001, t, 0.06); // square blip
  scheduleOsc('sine', 90, 55, 0.04, 0.0001, t, 0.08); // sub thump
}

// ─── Heavy Click Sound ──────────────────────────────────────────────────────
// A thicker, meatier click for main CTA buttons (like the login button)
export function playHeavyClickSound() {
  resumeCtx();
  const t = audioCtx.currentTime;
  scheduleNoise(0.25, t, 0.04);                            // louder white noise snap
  scheduleOsc('square', 300, 100, 0.08, 0.0001, t, 0.08); // lower, thicker square bite
  scheduleOsc('sine', 60, 30, 0.08, 0.0001, t, 0.12);     // deep, heavy sub kick
}

// ─── Send Sound ──────────────────────────────────────────────────────────────
// Ascending two-tone "whoosh" when a message is sent
export function playSendSound() {
  resumeCtx();
  const t = audioCtx.currentTime;
  scheduleNoise(0.08, t, 0.02);
  scheduleOsc('sine', 300, 900, 0.06, 0.0001, t, 0.12);
  scheduleOsc('sine', 600, 1800, 0.03, 0.0001, t + 0.04, 0.12);
}

// ─── Response Sound ──────────────────────────────────────────────────────────
// Soft descending chime when AI finishes responding
export function playResponseSound() {
  resumeCtx();
  const t = audioCtx.currentTime;
  scheduleOsc('sine', 880, 660, 0.05, 0.0001, t, 0.15);
  scheduleOsc('sine', 660, 440, 0.03, 0.0001, t + 0.1, 0.15);
  scheduleOsc('sine', 440, 330, 0.02, 0.0001, t + 0.22, 0.18);
}

// ─── Delete Sound ────────────────────────────────────────────────────────────
// Short low thud for destructive actions
export function playDeleteSound() {
  resumeCtx();
  const t = audioCtx.currentTime;
  scheduleNoise(0.12, t, 0.03);
  scheduleOsc('square', 180, 60, 0.05, 0.0001, t, 0.1);
}

// ─── Quick Action Sound ──────────────────────────────────────────────────────
// Bright blip for slash-command chips
export function playChipSound() {
  resumeCtx();
  const t = audioCtx.currentTime;
  scheduleOsc('square', 700, 1100, 0.04, 0.0001, t, 0.05);
  scheduleOsc('sine', 440, 880, 0.03, 0.0001, t + 0.03, 0.07);
}
