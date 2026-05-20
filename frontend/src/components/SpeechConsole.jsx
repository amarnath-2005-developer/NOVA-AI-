import React, { useEffect, useRef, useState } from 'react';
import './SpeechConsole.css';
import { sendCommand, transcribeAudio } from '../lib/api';
import { tts } from '../lib/tts';
import { createAudioCapture } from '../lib/audioCapture';

const SpeechConsole = () => {
  const [logs, setLogs] = useState([]);
  const [isListening, setIsListening] = useState(false);
  const [currentTranscript, setCurrentTranscript] = useState('');
  const [isMuted, setIsMuted] = useState(false);
  const [activeUser, setActiveUser] = useState(() => localStorage.getItem('nova_active_user') || 'amarnath');
  
  const consoleRef = useRef(null);
  const captureRef = useRef(null);
  const processingRef = useRef(false);
  const isListeningRef = useRef(false);
  const [isContinuous, setIsContinuous] = useState(false);
  const shouldBeListeningRef = useRef(false);
  const ttsSpeakingRef = useRef(false);
  const handleSilenceRef = useRef(null);

  // ── ECHO SUPPRESSION: Hard-lock mic during TTS ────────────────
  const speakAndResume = async (text) => {
    if (isMuted || !text) return;

    ttsSpeakingRef.current = true;
    if (isListeningRef.current && captureRef.current) {
        await captureRef.current.stop();
        isListeningRef.current = false;
        setIsListening(false);
    }
    
    // Ensure synthesis is active and not stuck
    if (window.speechSynthesis.paused) window.speechSynthesis.resume();
    
    await tts.speak(text);
    
    // Safety buffer for hardware/mic stabilization
    await new Promise(r => setTimeout(r, 400));

    ttsSpeakingRef.current = false;
    
    // Do not call resumeIfAuto here. Let the finally block in stopListeningAndProcess handle it.
  };

  useEffect(() => {
    // Sync active user across tabs/components
    const handleStorageChange = () => {
      const stored = localStorage.getItem('nova_active_user');
      if (stored && stored !== activeUser) setActiveUser(stored);
    };
    
    const pollBackend = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/v1/health");
        const data = await res.json();
        if (data.active_user && data.active_user !== activeUser) {
          setActiveUser(data.active_user);
          localStorage.setItem('nova_active_user', data.active_user);
        }
      } catch (e) {}
    };

    window.addEventListener('storage', handleStorageChange);
    const interval = setInterval(() => { handleStorageChange(); pollBackend(); }, 5000);
    return () => { window.removeEventListener('storage', handleStorageChange); clearInterval(interval); };
  }, [activeUser]);

  // VAD Callback Binding
  useEffect(() => {
      handleSilenceRef.current = () => {
          if (isListening && !processingRef.current) {
              stopListeningAndProcess();
          }
      };
  });

  useEffect(() => {
      createAudioCapture(() => {
          if (handleSilenceRef.current) handleSilenceRef.current();
      }).then(c => captureRef.current = c);

      return () => { if (captureRef.current) captureRef.current.destroy(); };
  }, []);

  const resumeIfAuto = () => {
      processingRef.current = false;
      if (!shouldBeListeningRef.current) return;

      // Rely only on internal ttsSpeakingRef for higher reliability
      if (!ttsSpeakingRef.current) {
         setTimeout(() => {  // Reduced delay for snappier re-listen
             if (shouldBeListeningRef.current) startListening();
         }, 150);
      } else {
         // Retry in 500ms if our internal flag is still set
         setTimeout(resumeIfAuto, 500);
      }
  };

  const startListening = () => {
    try {
        // Use the ref to prevent React stale closure bugs in async loops
        if (captureRef.current && !isListeningRef.current && !ttsSpeakingRef.current) {
          if (window.speechSynthesis.paused) window.speechSynthesis.resume();
          
          shouldBeListeningRef.current = true;
          setIsContinuous(true);
          processingRef.current = false;
          
          captureRef.current.start();
          
          isListeningRef.current = true;
          setIsListening(true);
          
          window.dispatchEvent(new CustomEvent('nova-listening-start'));
          setCurrentTranscript('NOVA_LISTENING...');
        }
    } catch(err) {
        console.error("Failed to start listening:", err);
        setCurrentTranscript('System Error. Please click Listen.');
    }
  };

  const stopListeningAndProcess = async () => {
    if (!isListeningRef.current || !captureRef.current || processingRef.current) return;
    
    processingRef.current = true;
    isListeningRef.current = false;
    setIsListening(false);
    window.dispatchEvent(new CustomEvent('nova-listening-stop'));
    
    let shouldResume = true;

    try {
        const audioBlob = await captureRef.current.stop();
        
        if (audioBlob.size < 1000) {
            setCurrentTranscript('');
            return;
        }

        setCurrentTranscript('Transcribing via Neural Core (Groq Whisper)...');
        const transResponse = await transcribeAudio(audioBlob);
        const text = transResponse.transcript;
        
        const lowerText = text.toLowerCase();
        const isStopCommand = lowerText.includes("it's time to sleep") || 
                              lowerText.includes('sleep mode') || 
                              lowerText.includes('nova stop') ||
                              lowerText.includes('stop listening') ||
                              lowerText === 'stop' || lowerText === 'stop.' ||
                              lowerText.includes('standby');

        if (isStopCommand) {
            setCurrentTranscript('ENTERING_SLEEP_MODE...');
            shouldBeListeningRef.current = false;
            setIsContinuous(false);
            isListeningRef.current = false;
            setIsListening(false);
            
            const sleepId = Date.now();
            setLogs(prev => [...prev, { speaker: 'USER', text: text, id: sleepId }]);
            
            await speakAndResume("Understood. Entering sleep mode. Systems powering down.");
            setCurrentTranscript('');
            shouldResume = false;
            
            // Clear the console after speaking so it "vanishes"
            setTimeout(() => {
                setLogs([]);
            }, 2000);
            
            return;
        }

        if (!text || text.trim() === "") {
            setCurrentTranscript('');
            return;
        }

        const id = Date.now();
        setLogs(prev => [...prev, { speaker: 'USER', text: text, id }]);
        setCurrentTranscript('Neural Processing...');

        const response = await sendCommand(text);
        
        if (response.active_user && response.active_user !== activeUser) {
          setActiveUser(response.active_user);
          localStorage.setItem('nova_active_user', response.active_user);
        }

        // Dispatch PDF summary event to display the glassmorphic modal
        if (response.success && response.result && response.result.metadata && response.result.metadata.pdf_summary) {
          window.dispatchEvent(new CustomEvent('nova-pdf-summary', {
            detail: response.result.metadata.pdf_summary
          }));
        }
        
        const novaId = Date.now() + 1;
        setLogs(prev => [...prev, { speaker: 'NOVA', text: response.result.response_message, id: novaId }]);
        
        setCurrentTranscript('NOVA_SPEAKING...');
        await speakAndResume(response.result.response_message);
        setCurrentTranscript('');
        
        setTimeout(() => {
          setLogs(prev => prev.filter(log => log.id !== id && log.id !== novaId));
        }, 15000);

    } catch(err) {
        setCurrentTranscript('Recovering system...');
        console.error("Audio process failed:", err);
    } finally {
        processingRef.current = false;
        if (shouldResume && shouldBeListeningRef.current) {
            setTimeout(resumeIfAuto, 500);
        } else if (!shouldResume) {
            isListeningRef.current = false;
            setIsListening(false);
        }
    }
  };

  const manualStop = () => {
      shouldBeListeningRef.current = false;
      setIsContinuous(false);
      if (isListeningRef.current) stopListeningAndProcess();
  };

  useEffect(() => {
    if (consoleRef.current) {
      consoleRef.current.scrollTop = consoleRef.current.scrollHeight;
    }
  }, [logs, currentTranscript]);

  return (
    <div className="speech-console-container">
      <div className="console-header">
        <div className="title">
          <div className={`header-dot ${isListening ? 'active' : ''}`}></div>
          SYSTEM_LOG // N.O.V.A. {isContinuous ? '[CONTINUOUS_ACTIVE]' : ''}
        </div>
        <div className="active-user-badge" style={{
          marginLeft: 'auto', marginRight: '15px', padding: '2px 8px',
          background: 'rgba(0, 255, 255, 0.1)', border: '1px solid rgba(0, 255, 255, 0.3)',
          borderRadius: '4px', fontSize: '10px', textTransform: 'uppercase',
          letterSpacing: '1px', color: '#0ff'
        }}>
          USER: {activeUser}
        </div>
        <div className="controls">
          <button className="control-btn" onClick={() => { tts.setMute(!isMuted); setIsMuted(!isMuted); }}>
            {isMuted ? 'UNMUTE' : 'MUTE'}
          </button>
          <button className="control-btn" onClick={isListening ? manualStop : startListening}>
            {isListening ? 'STOP' : 'LISTEN'}
          </button>
        </div>
      </div>

      <div className="console-content" ref={consoleRef}>
        {logs.map((log) => (
          <div key={log.id} className="log-entry">
            <span className="prefix">&gt;</span>
            <span className="speaker">{log.speaker} &gt;</span>
            <span className={`message ${log.speaker === 'NOVA' ? 'nova-message' : ''}`}>
              {log.text}
            </span>
          </div>
        ))}
        
        {currentTranscript && (
          <div className="log-entry">
            <span className="prefix">&gt;</span>
            <span className="speaker">SYS &gt;</span>
            <span className="message" style={{ color: '#0ff', opacity: 0.8 }}>{currentTranscript}</span>
            <div className="block-cursor"></div>
          </div>
        )}

        {!currentTranscript && logs.length === 0 && (
          <div className="log-entry">
            <span className="prefix">&gt;</span>
            <span className="message" style={{ opacity: 0.4 }}>AWAITING COMMAND INPUT...</span>
            <div className="block-cursor"></div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SpeechConsole;
