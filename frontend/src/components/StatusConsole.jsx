import React, { useEffect, useState } from 'react';
import './StatusConsole.css';
import { API_BASE_URL } from '../lib/api';

const StatusConsole = () => {
  const [data, setData] = useState({
    latency: '0ms',
    load: '0%',
    tasks: 0,
    systems: {
      core: 'loading',
      neural: 'loading',
      stt: 'loading',
      os_commands: 'loading',
      vault: 'loading'
    }
  });
  const [logs, setLogs] = useState([]);
  const [isMinimized, setIsMinimized] = useState(false);

  const addLog = (message, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString([], { hour12: false });
    setLogs(prev => [{ timestamp, message, type }, ...prev].slice(0, 10));
  };

  const fetchStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      if (response.ok) {
        const newData = await response.json();
        setData(newData);
        if (data.systems.core === 'loading') {
          addLog('Neural link established with Core', 'success');
        }
      } else {
        throw new Error('API Unreachable');
      }
    } catch (err) {
      setData(prev => ({
        ...prev,
        systems: { core: 'offline', neural: 'offline', stt: 'offline', os_commands: 'offline', vault: 'offline' }
      }));
      addLog('Neural link disrupted: API Unreachable', 'error');
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status) => {
    switch (status) {
      case 'connected':
      case 'active':
      case 'ready':
      case 'authorized':
      case 'linked':
        return '#0f0';
      case 'loading':
        return '#f90';
      case 'offline':
        return '#f00';
      default:
        return '#3acaec';
    }
  };

  return (
    <div className={`status-console-container ${isMinimized ? 'minimized' : ''}`}>
      <div className="status-header">
        <span>
          <div className="header-dot pulse"></div>
          SYSTEM TELEMETRY
        </span>
        <button className="minimize-btn" onClick={() => setIsMinimized(!isMinimized)}>
          {isMinimized ? '□' : '—'}
        </button>
      </div>

      {!isMinimized && (
        <div className="status-body">
          <div className="telemetry-section">
            <div className="section-title">METRICS</div>
            <div className="metrics-row">
              <div className="metric">
                <span className="m-label">LATENCY</span>
                <span className="m-value">{data.latency}</span>
              </div>
              <div className="metric">
                <span className="m-label">LOAD</span>
                <span className="m-value">{data.load}</span>
              </div>
              <div className="metric">
                <span className="m-label">CPU</span>
                <span className="m-value">{data.cpu || '0%'}</span>
              </div>
            </div>
          </div>

          <div className="telemetry-section">
            <div className="section-title">SUB-SYSTEMS</div>
            <div className="status-grid">
              {Object.entries(data.systems).map(([key, value]) => (
                <div key={key} className="status-item">
                  <div className="dot" style={{ background: getStatusColor(value), boxShadow: `0 0 5px ${getStatusColor(value)}` }}></div>
                  <span className="label">{key.replace('_', '-').toUpperCase()}:</span>
                  <span className="value" style={{ color: getStatusColor(value) }}>{value.toUpperCase()}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="status-logs">
            {logs.map((log, idx) => (
              <div key={idx} className={`log-entry ${log.type}`}>
                <span className="time">[{log.timestamp}]</span> {log.message}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default StatusConsole;
