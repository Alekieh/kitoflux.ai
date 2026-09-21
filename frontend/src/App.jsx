import React, { useState, useEffect, useRef } from 'react';

export default function App() {
  const [missionState, setMissionState] = useState('INITIALIZED');
  const [transcripts, setTranscripts] = useState([]);
  const [suggestion, setSuggestion] = useState(null);
  const [streamingText, setStreamingText] = useState('');
  const [latency, setLatency] = useState(312);
  const [stealthActive, setStealthActive] = useState(true);
  const [autotypeStatus, setAutotypeStatus] = useState('ARMED');
  const [micActive, setMicActive] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  // Settings state
  const [groqKey, setGroqKey] = useState('');
  const [openaiKey, setOpenaiKey] = useState('');
  const [provider, setProvider] = useState('groq');
  const [persona, setPersona] = useState('Senior Systems Architect');
  const [resumeText, setResumeText] = useState('');

  const wsRef = useRef(null);
  const recognitionRef = useRef(null);
  const transcriptEndRef = useRef(null);

  // 1. Connect WebSocket to Python Kernel
  useEffect(() => {
    const connectWS = () => {
      const socket = new WebSocket('ws://127.0.0.1:8765/ws');
      wsRef.current = socket;

      socket.onopen = () => {
        console.log('[Kernel WS] Connected to Kitoflux Core Kernel');
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleServerEvent(data);
        } catch (e) {
          console.error('[WS Parse Error]:', e);
        }
      };

      socket.onclose = () => {
        console.log('[Kernel WS] Disconnected. Reconnecting in 2s...');
        setTimeout(connectWS, 2000);
      };
    };

    connectWS();

    // Check stealth status from Electron bridge if available
    if (window.kitoflux) {
      window.kitoflux.getStealthStatus().then((status) => setStealthActive(status));
      window.kitoflux.onGlobalHotkey((event) => {
        if (event === 'TRIGGER_AUTOTYPE') {
          handleTriggerAutotype();
        }
      });
    }

    return () => {
      if (wsRef.current) wsRef.current.close();
      if (recognitionRef.current) recognitionRef.current.stop();
    };
  }, []);

  // 2. Handle events from Python kernel
  const handleServerEvent = (data) => {
    switch (data.type) {
      case 'INITIAL_SYNC':
        if (data.state) setMissionState(data.state);
        if (data.transcript_history) setTranscripts(data.transcript_history);
        if (data.current_suggestion) setSuggestion(data.current_suggestion);
        break;
      case 'MISSION_STATE':
        setMissionState(data.state);
        break;
      case 'TRANSCRIPT_UPDATE':
        setTranscripts((prev) => [...prev.slice(-25), data.segment]);
        break;
      case 'REASONING_START':
        setStreamingText('');
        setSuggestion({
          query: data.query,
          citations: data.citations || [],
          summary: 'Generating tactical guidance...',
          bullet_points: [],
          confidence_score: 0.95
        });
        break;
      case 'REASONING_TOKEN':
        setStreamingText((prev) => prev + data.token);
        break;
      case 'REASONING_COMPLETE':
        setSuggestion(data.suggestion);
        setStreamingText('');
        if (data.latency_ms) setLatency(data.latency_ms);
        break;
      case 'AUTOTYPE_STATUS':
        setAutotypeStatus(data.status);
        break;
      default:
        break;
    }
  };

  // Scroll transcript down automatically
  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [transcripts]);

  // 3. Web Speech API Microphone Bridge
  const toggleMicrophone = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('Speech Recognition is supported directly in Chromium/Electron. Running in web mode.');
      return;
    }

    if (micActive) {
      if (recognitionRef.current) recognitionRef.current.stop();
      setMicActive(false);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onresult = (event) => {
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const result = event.results[i];
          const text = result[0].transcript;
          const isFinal = result.isFinal;

          if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
              type: 'TRANSCRIPT_CHUNK',
              text: text,
              is_final: isFinal,
              speaker: 'INTERVIEWER'
            }));
          }
        }
      };

      recognition.onerror = (err) => {
        console.error('[SpeechRecognition Error]:', err);
      };

      recognition.onend = () => {
        if (micActive) recognition.start(); // Auto-restart
      };

      recognition.start();
      recognitionRef.current = recognition;
      setMicActive(true);
      setMissionState('LISTENING');
    } catch (e) {
      console.error('[Speech Init Error]:', e);
    }
  };

  // 4. Trigger Autotyper
  const handleTriggerAutotype = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'TRIGGER_AUTOTYPE'
      }));
    }
  };

  // 5. Save Settings & Knowledge to Backend
  const handleSaveSettings = async () => {
    try {
      await fetch('http://127.0.0.1:8765/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          groq_api_key: groqKey || undefined,
          openai_api_key: openaiKey || undefined,
          llm_provider: provider
        })
      });

      if (resumeText.trim()) {
        await fetch('http://127.0.0.1:8765/api/knowledge/upload', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title: 'Operator_Profile_Resume',
            content: resumeText,
            doc_type: 'RESUME'
          })
        });
      }
      setShowSettings(false);
    } catch (err) {
      console.error('[Save Settings Error]:', err);
      setShowSettings(false);
    }
  };

  return (
    <div className="hud-container">
      {/* HUD Header Bar */}
      <div className="hud-header">
        <div className="logo-badge">
          <span>KITOFLUX.AI</span>
        </div>

        <div className="hud-status-pills">
          <div className={`pill ${missionState === 'REASONING' ? 'pill-blue' : 'pill-green'}`}>
            <span className="pulse-dot"></span>
            <span>{missionState}</span>
          </div>

          <div className="pill pill-blue">
            <span>{latency}ms</span>
          </div>

          <div className={`pill ${stealthActive ? 'pill-green' : 'pill-amber'}`}>
            <span>{stealthActive ? 'WDA_EXCLUDE' : 'VISIBLE'}</span>
          </div>
        </div>

        <div className="no-drag" style={{ display: 'flex', gap: '6px' }}>
          <button 
            className={`btn ${micActive ? 'btn' : 'btn-secondary'}`} 
            style={{ padding: '3px 9px', fontSize: '11px' }}
            onClick={toggleMicrophone}
          >
            {micActive ? 'Mic: ON' : 'Mic: OFF'}
          </button>
          
          <button 
            className="btn btn-secondary" 
            style={{ padding: '3px 9px', fontSize: '11px' }}
            onClick={() => setShowSettings(true)}
          >
            Config
          </button>

          <button 
            className="btn btn-secondary" 
            style={{ padding: '3px 9px', fontSize: '11px', background: 'rgba(239, 68, 68, 0.25)', color: '#f87171' }}
            onClick={() => window.kitoflux?.panicHide()}
            title="Panic Hide HUD (Ctrl+Shift+X)"
          >
            Hide
          </button>
        </div>
      </div>

      {/* HUD Body */}
      <div className="hud-body">
        {/* Channel 1: Live Transcript Stream */}
        <div className="channel-card">
          <div className="channel-header">
            <span>Channel 1: Live Transcript Stream</span>
            <span>{transcripts.length} segments</span>
          </div>
          <div className="channel-transcript">
            {transcripts.length === 0 ? (
              <span style={{ color: '#6b7280', fontStyle: 'italic' }}>
                Awaiting incoming speech telemetry. Toggle 'Mic: ON' or capture loopback audio...
              </span>
            ) : (
              transcripts.map((t, idx) => (
                <div key={idx} style={{ marginBottom: '3px' }}>
                  <span style={{ color: t.speaker === 'INTERVIEWER' ? '#38bdf8' : '#a78bfa', fontWeight: 600 }}>
                    {t.speaker === 'INTERVIEWER' ? 'Caller: ' : 'You: '}
                  </span>
                  <span>{t.text}</span>
                </div>
              ))
            )}
            <div ref={transcriptEndRef} />
          </div>
        </div>

        {/* Channel 2: Strategic Reasoning Stream */}
        <div className="channel-card channel-reasoning">
          <div className="channel-header">
            <span>Channel 2: Strategic Reasoning Stream</span>
            {suggestion && (
              <span style={{ color: '#34d399' }}>
                Confidence: {Math.round(suggestion.confidence_score * 100)}%
              </span>
            )}
          </div>

          {streamingText ? (
            <div style={{ whiteSpace: 'pre-wrap', color: '#e5e7eb' }}>
              {streamingText}
              <span className="pulse-dot" style={{ display: 'inline-block', marginLeft: '4px' }}></span>
            </div>
          ) : suggestion ? (
            <div>
              {suggestion.summary && (
                <div className="reasoning-takeaway">
                  {suggestion.summary}
                </div>
              )}

              {suggestion.bullet_points && suggestion.bullet_points.length > 0 && (
                <ul className="reasoning-bullets">
                  {suggestion.bullet_points.map((pt, i) => (
                    <li key={i}>{pt}</li>
                  ))}
                </ul>
              )}

              {suggestion.code_snippet && (
                <div className="code-block">
                  <pre>{suggestion.code_snippet}</pre>
                </div>
              )}

              {suggestion.citations && suggestion.citations.length > 0 && (
                <div style={{ marginTop: '8px', display: 'flex', gap: '6px' }}>
                  {suggestion.citations.map((c, i) => (
                    <span key={i} className="pill pill-blue" style={{ fontSize: '10px' }}>
                      Ref: {c}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div style={{ color: '#6b7280', fontStyle: 'italic' }}>
              Standing by. When an interview question is detected, real-time tactical reasoning will project here.
            </div>
          )}
        </div>

        {/* Channel 3: Humanized Autotyper Telemetry */}
        <div className="channel-card channel-autotyper">
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '11px', fontWeight: 600, color: '#9ca3af' }}>
              Channel 3: Autotyper Telemetry
            </span>
            <span style={{ fontSize: '12px', color: autotypeStatus === 'IN_PROGRESS' ? '#38bdf8' : '#34d399' }}>
              Status: <strong>{autotypeStatus}</strong> | Shortcut: <code>Ctrl+Shift+Space</code>
            </span>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <button 
              className="btn" 
              onClick={handleTriggerAutotype}
              disabled={autotypeStatus === 'IN_PROGRESS'}
            >
              {autotypeStatus === 'IN_PROGRESS' ? 'Typing...' : 'Simulate Autotype'}
            </button>
          </div>
        </div>
      </div>

      {/* Settings Modal */}
      {showSettings && (
        <div className="modal-backdrop">
          <div className="modal-content">
            <h3 style={{ fontSize: '14px', fontWeight: 700, color: '#00f2fe' }}>
              KITOFLUX.AI Configuration
            </h3>

            <div>
              <label style={{ fontSize: '11px', color: '#9ca3af' }}>LLM Provider</label>
              <select 
                value={provider} 
                onChange={(e) => setProvider(e.target.value)}
                style={{ width: '100%', marginTop: '4px' }}
              >
                <option value="groq">Groq (Ultra-Low Latency / Llama-3)</option>
                <option value="openai">OpenAI (GPT-4o-mini)</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: '11px', color: '#9ca3af' }}>Groq API Key (Optional)</label>
              <input 
                type="password"
                placeholder="gsk_..."
                value={groqKey}
                onChange={(e) => setGroqKey(e.target.value)}
                style={{ width: '100%', marginTop: '4px' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '11px', color: '#9ca3af' }}>OpenAI API Key (Optional)</label>
              <input 
                type="password"
                placeholder="sk-..."
                value={openaiKey}
                onChange={(e) => setOpenaiKey(e.target.value)}
                style={{ width: '100%', marginTop: '4px' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '11px', color: '#9ca3af' }}>Operator Persona / Target Role</label>
              <input 
                type="text"
                value={persona}
                onChange={(e) => setPersona(e.target.value)}
                style={{ width: '100%', marginTop: '4px' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '11px', color: '#9ca3af' }}>Knowledge RAG Context (Paste Resume / Job Specs)</label>
              <textarea 
                rows="4"
                placeholder="Paste key achievements, previous roles, or tech stack points to ground the AI responses..."
                value={resumeText}
                onChange={(e) => setResumeText(e.target.value)}
                style={{ width: '100%', marginTop: '4px' }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '8px' }}>
              <button className="btn btn-secondary" onClick={() => setShowSettings(false)}>
                Cancel
              </button>
              <button className="btn" onClick={handleSaveSettings}>
                Save & Initialize
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
