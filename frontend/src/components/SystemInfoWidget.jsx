import React, { useState, useEffect } from 'react';
import './SystemInfoWidget.css';

const SystemInfoWidget = () => {
  const [time, setTime] = useState(new Date());
  const [stats, setStats] = useState({ uptime: '0h 0m', commands: 0 });
  const [weather, setWeather] = useState({ temp: '--', condition: 'SYNCING...', city: 'LOCATING...' });

  const fetchWeatherData = async () => {
    try {
      // PROXY THROUGH BACKEND to avoid CORS/IP blocks
      const response = await fetch('http://127.0.0.1:8000/api/v1/telemetry/weather');
      if (response.ok) {
        const data = await response.json();
        
        const conditions = {
          0: 'CLEAR',
          1: 'MAINLY CLEAR', 2: 'PARTLY CLOUDY', 3: 'OVERCAST',
          45: 'FOGGY', 48: 'FOGGY',
          51: 'DRIZZLE', 61: 'RAINY',
          71: 'SNOWY', 95: 'THUNDER'
        };

        setWeather({
          temp: data.temp,
          condition: conditions[data.code] || 'CLEAR',
          city: data.city
        });
      } else {
        throw new Error("Backend proxy failed");
      }
    } catch (err) {
      console.error("Weather sync failed", err);
      setWeather(prev => ({ ...prev, condition: 'OFFLINE' }));
    }
  };

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    
    const fetchStats = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/api/v1/health');
        if (response.ok) {
          const data = await response.json();
          setStats({ uptime: data.uptime, commands: data.commands });
        }
      } catch (err) {
        console.error("Widget stats failed", err);
      }
    };

    fetchStats();
    fetchWeatherData();
    
    const statsInterval = setInterval(fetchStats, 10000);
    const weatherInterval = setInterval(fetchWeatherData, 600000); 

    return () => {
      clearInterval(timer);
      clearInterval(statsInterval);
      clearInterval(weatherInterval);
    };
  }, []);

  const formatTime = (date) => {
    const hh = String(date.getHours()).padStart(2, '0');
    const mm = String(date.getMinutes()).padStart(2, '0');
    const ss = String(date.getSeconds()).padStart(2, '0');
    return { hh, mm, ss };
  };

  const formatDate = (date) => {
    const options = { weekday: 'short', month: 'short', day: 'numeric' };
    return date.toLocaleDateString('en-US', options).toUpperCase();
  };

  const { hh, mm, ss } = formatTime(time);

  return (
    <div className="system-info-widget">
      <div className="widget-header">
        <span className="title">SYSTEM_INFO</span>
        <div className="status-indicator"></div>
      </div>

      <div className="clock-section">
        <div className="time-display">
          <span className="large">{hh}:{mm}</span>
          <span className="small">:{ss}</span>
        </div>
        <div className="date-display">{formatDate(time)}</div>
      </div>

      <div className="divider">
        <div className="diamond"></div>
      </div>

      <div className="weather-section">
        <div className="weather-main">
          <span className="icon">{weather.temp !== '--' ? '🌤️' : '⏳'}</span>
          <span className="temp">{weather.temp}</span>
        </div>
        <div className="condition">{weather.condition}</div>
      </div>

      <div className="divider">
        <div className="diamond"></div>
      </div>

      <div className="location-section">
        <span className="pin">📍</span>
        <span className="city">{weather.city}</span>
      </div>

      <div className="divider">
        <div className="diamond"></div>
      </div>

      <div className="stats-grid">
        <div className="stat-box">
          <span className="s-label">UPTIME</span>
          <span className="s-value">{stats.uptime}</span>
        </div>
        <div className="stat-box">
          <span className="s-label">COMMANDS</span>
          <span className="s-value">{stats.commands}</span>
        </div>
      </div>
    </div>
  );
};

export default SystemInfoWidget;
