import React, { useEffect, useRef } from 'react';
import { liquidMetalFragmentShader, ShaderMount } from '@paper-design/shaders';
import './Navbar.css';

export default function Navbar({ onNavigate, currentView }) {
  const brandRef = useRef(null);
  const loginRef = useRef(null);
  const settingsRef = useRef(null);

  useEffect(() => {
    let brandMount;
    let loginMount;
    let settingsMount;

    const shaderConfig = {
      u_repetition: 1.5,
      u_softness: 0.5,
      u_shiftRed: 0.3,
      u_shiftBlue: 0.3,
      u_distortion: 0.1,
      u_contour: 0.1,
      u_angle: 100,
      u_scale: 1.5,
      u_shape: 1,
      u_offsetX: 0.1,
      u_offsetY: -0.1
    };

    if (brandRef.current) {
      try {
        brandMount = new ShaderMount(
          brandRef.current,
          liquidMetalFragmentShader,
          shaderConfig,
          undefined,
          0.6
        );
      } catch (err) {
        console.error("Brand shader failed:", err);
      }
    }

    if (loginRef.current) {
      try {
        loginMount = new ShaderMount(
          loginRef.current,
          liquidMetalFragmentShader,
          shaderConfig,
          undefined,
          0.6
        );
      } catch (err) {
        console.error("Login shader failed:", err);
      }
    }

    if (settingsRef.current) {
      try {
        settingsMount = new ShaderMount(
          settingsRef.current,
          liquidMetalFragmentShader,
          shaderConfig,
          undefined,
          0.6
        );
      } catch (err) {
        console.error("Settings shader failed:", err);
      }
    }

    return () => {
      if (brandMount) {
        if (typeof brandMount.destroy === 'function') brandMount.destroy();
        else if (typeof brandMount.dispose === 'function') brandMount.dispose();
      }
      if (loginMount) {
        if (typeof loginMount.destroy === 'function') loginMount.destroy();
        else if (typeof loginMount.dispose === 'function') loginMount.dispose();
      }
      if (settingsMount) {
        if (typeof settingsMount.destroy === 'function') settingsMount.destroy();
        else if (typeof settingsMount.dispose === 'function') settingsMount.dispose();
      }
      if (brandRef.current) {
        brandRef.current.querySelectorAll("canvas").forEach(canvas => canvas.remove());
      }
      if (loginRef.current) {
        loginRef.current.querySelectorAll("canvas").forEach(canvas => canvas.remove());
      }
      if (settingsRef.current) {
        settingsRef.current.querySelectorAll("canvas").forEach(canvas => canvas.remove());
      }
    };
  }, []);

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        {/* Brand Name on the Left as a Liquid Button */}
        <div className="nav-left">
          <button 
            className={`nav-liquid-btn brand-btn ${currentView === 'home' ? 'active' : ''}`}
            onClick={() => onNavigate('home')}
          >
            <div className="liquid-bg" ref={brandRef}></div>
            <div className="btn-outline"></div>
            <span className="btn-text">NOVA AI</span>
          </button>
        </div>

        {/* Center: Login Button */}
        <div className="nav-center">
          <button 
            className={`nav-liquid-btn ${currentView === 'login' ? 'active' : ''}`}
            onClick={() => onNavigate('login')}
          >
            <div className="liquid-bg" ref={loginRef}></div>
            <div className="btn-outline"></div>
            <span className="btn-text">Login</span>
          </button>
        </div>

        {/* Right: Settings Button */}
        <div className="nav-right">
          <button 
            className={`nav-liquid-btn ${currentView === 'settings' ? 'active' : ''}`}
            onClick={() => onNavigate('settings')}
          >
            <div className="liquid-bg" ref={settingsRef}></div>
            <div className="btn-outline"></div>
            <span className="btn-text">Settings</span>
          </button>
        </div>
      </div>
    </nav>
  );
}
