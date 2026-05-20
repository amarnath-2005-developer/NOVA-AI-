import React, { useState, useEffect } from 'react';
import './ActivityMonitorPanel.css';

const ActivityMonitorPanel = () => {
  const [isListening, setIsListening] = useState(false);
  const [history, setHistory] = useState([
    { time: new Date().toLocaleTimeString([], { hour12: false }), status: 'SYSTEM READY' }
  ]);

  useEffect(() => {
    const onStart = () => setIsListening(true);
    const onStop = () => setIsListening(false);

    window.addEventListener('nova-listening-start', onStart);
    window.addEventListener('nova-listening-stop', onStop);

    return () => {
      window.removeEventListener('nova-listening-start', onStart);
      window.removeEventListener('nova-listening-stop', onStop);
    };
  }, []);

  useEffect(() => {
    if (isListening) {
      addEvent('LISTENING');
    } else {
      addEvent('STANDBY');
    }
  }, [isListening]);

  const addEvent = (status) => {
    const time = new Date().toLocaleTimeString([], { hour12: false });
    setHistory(prev => [{ time, status }, ...prev].slice(0, 5));
  };

  return (
    <div className="activity-monitor-panel">
      <div className="panel-header">
        <span>ACTIVITY MONITOR</span>
        <div className="pulse-dot"></div>
      </div>

      <div className={`status-banner ${isListening ? 'active' : ''}`}>
        <span className="icon">{isListening ? '👂' : '💤'}</span>
        <span className="text">{isListening ? 'LISTENING' : 'STANDBY'}</span>
      </div>

      <div className="activity-history">
        {history.map((entry, idx) => (
          <div key={idx} className="history-item">
            <span className="time">{entry.time}</span>
            <span className="arrow">→</span>
            <span className={`status ${entry.status === 'LISTENING' ? 'highlight' : ''}`}>
              {entry.status}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ActivityMonitorPanel;
