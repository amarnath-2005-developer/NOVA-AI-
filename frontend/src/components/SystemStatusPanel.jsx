import React, { useState, useEffect } from 'react';
import './SystemStatusPanel.css';

const SystemStatusPanel = () => {
  const [battery, setBattery] = useState({ level: 0, charging: false });
  const [network, setNetwork] = useState(navigator.onLine ? 'ONLINE' : 'OFFLINE');

  useEffect(() => {
    // Battery Status API
    if (navigator.getBattery) {
      navigator.getBattery().then(batt => {
        setBattery({ level: Math.round(batt.level * 100), charging: batt.charging });
        batt.addEventListener('levelchange', () => setBattery(prev => ({ ...prev, level: Math.round(batt.level * 100) })));
        batt.addEventListener('chargingchange', () => setBattery(prev => ({ ...prev, charging: batt.charging })));
      });
    }

    // Network Status
    const updateOnlineStatus = () => setNetwork(navigator.onLine ? 'ONLINE' : 'OFFLINE');
    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);

    return () => {
      window.removeEventListener('online', updateOnlineStatus);
      window.removeEventListener('offline', updateOnlineStatus);
    };
  }, []);

  return (
    <div className="system-status-panel">
      <div className="panel-header">SYSTEM STATUS</div>
      <div className="status-grid-2x2">
        <div className="status-box">
          <div className="box-icon">🔌</div>
          <div className="box-info">
            <span className="label">BATTERY</span>
            <span className="value" style={{ color: battery.level > 20 ? '#0f0' : '#f00' }}>
              {battery.level}% {battery.charging ? '⚡' : ''}
            </span>
          </div>
        </div>

        <div className="status-box">
          <div className="box-icon">🌐</div>
          <div className="box-info">
            <span className="label">NETWORK</span>
            <span className="value" style={{ color: network === 'ONLINE' ? '#0f0' : '#f00' }}>
              {network}
            </span>
          </div>
        </div>

        <div className="status-box">
          <div className="box-icon">📡</div>
          <div className="box-info">
            <span className="label">CONNECTION</span>
            <span className="value">4G / WiFi</span>
          </div>
        </div>

        <div className="status-box">
          <div className="box-icon">🔵</div>
          <div className="box-info">
            <span className="label">BLUETOOTH</span>
            <span className="value" style={{ color: '#0f0' }}>READY</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemStatusPanel;
