import { useState, useRef } from 'react';
import './InputBar.css';
import { playClickSound, playSendSound, playChipSound } from '../utils/sound';

const QUICK_ACTIONS = [
  { label: '/task', prompt: 'Add a task: ' },
  { label: '/schedule', prompt: 'Schedule an event: ' },
  { label: '/drive', prompt: 'Organize my Google Drive.' },
  { label: '/email', prompt: 'Send an email to ' },
  { label: '/brief', prompt: "Give me today's briefing." },
];

function InputBar({ onSend, disabled }) {
  const [text, setText] = useState('');
  const [imageFile, setImageFile] = useState(null);
  const fileRef = useRef(null);
  const inputRef = useRef(null);

  function handleSubmit(e) {
    e.preventDefault();
    if (!text.trim() && !imageFile) return;
    playSendSound();
    onSend(text, imageFile);
    setText('');
    setImageFile(null);
    if (fileRef.current) fileRef.current.value = '';
  }

  function handleQuickAction(prompt) {
    playChipSound();
    setText(prompt);
    // Focus the input so user can type the rest
    setTimeout(() => inputRef.current?.focus(), 0);
  }

  return (
    <div className="input-area">
      {/* Quick actions row */}
      <div className="quick-actions">
        {QUICK_ACTIONS.map((qa) => (
          <button
            key={qa.label}
            className="quick-action-chip"
            onClick={() => handleQuickAction(qa.prompt)}
            disabled={disabled}
            tabIndex={-1}
          >
            {qa.label}
          </button>
        ))}
      </div>

      {imageFile && (
        <div className="input-preview">
          <span>📎 {imageFile.name}</span>
          <button onClick={() => { setImageFile(null); fileRef.current.value = ''; }}>✕</button>
        </div>
      )}

      <form className="input-row" onSubmit={handleSubmit}>
        <label className="input-upload" title="Attach file" onClick={playClickSound}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
          </svg>
          <input type="file" ref={fileRef} accept="image/*,.pdf,.txt,.csv,.doc,.docx" style={{ display: 'none' }}
            onChange={(e) => e.target.files[0] && setImageFile(e.target.files[0])} />
        </label>

        <span className="input-prompt pixel-text">›</span>

        <input
          ref={inputRef}
          type="text"
          className="input-field"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Message Caleminder..."
          disabled={disabled}
          autoComplete="off"
        />

        <button type="submit" className="input-send" disabled={disabled || (!text.trim() && !imageFile)}>
          {disabled ? (
            <span className="input-spinner" />
          ) : (
            <svg width="15" height="15" viewBox="0 0 24 24" fill="white" stroke="none">
              <path d="M2 21l21-9L2 3v7l15 2-15 2z" />
            </svg>
          )}
        </button>
      </form>
    </div>
  );
}

export default InputBar;
