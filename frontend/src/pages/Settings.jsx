import React, { useState, useEffect, useRef } from 'react';
import { 
  Brain, Mic, Cpu, Zap, Eye, HeartPulse, Wrench, Shield, Gauge, Link, Terminal, Flame,
  Save, ChevronRight, ChevronLeft, ChevronDown, CheckCircle2, AlertCircle, RefreshCw, Layers,
  Check, X, AlertTriangle, Key, HardDrive, Layout, RefreshCcw, Wifi, HelpCircle, Menu, Play, Code, Lock
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import './Settings.css';
import { API_BASE_URL } from '../lib/api';

// --- NEURAL DROPDOWN COMPONENT ---
const NeuralDropdown = ({ options, value, onChange }) => {
  const [isOpen, setIsOpen] = useState(false);
  
  return (
    <div className="neural-dropdown-container">
      <button 
        className={`neural-dropdown-trigger ${isOpen ? 'open' : ''}`}
        onClick={() => setIsOpen(!isOpen)}
      >
        <span>{value || 'Select option...'}</span>
        <ChevronDown size={16} className={`dropdown-arrow ${isOpen ? 'rotated' : ''}`} />
      </button>
      
      <AnimatePresence>
        {isOpen && (
          <motion.div 
            className="neural-dropdown-menu"
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
          >
            {options.map((opt, i) => (
              <button 
                key={i}
                className={`dropdown-item ${value === opt ? 'selected' : ''}`}
                onClick={() => {
                  onChange(opt);
                  setIsOpen(false);
                }}
              >
                {opt}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

// --- WIDGET 1: COGNITIVE CORE GRAPH (AI Core) ---
const CognitiveCoreGraph = ({ depth, temp }) => {
  const [pulses, setPulses] = useState([]);
  
  useEffect(() => {
    const pulseCount = depth === 'Low' ? 1 : depth === 'Medium' ? 2 : depth === 'Deep' ? 4 : 6;
    const interval = setInterval(() => {
      setPulses(prev => {
        const newPulse = {
          id: Math.random(),
          scale: 0.2,
          opacity: 0.8
        };
        return [...prev.slice(-5), newPulse];
      });
    }, 1500 / (pulseCount * temp));

    return () => clearInterval(interval);
  }, [depth, temp]);

  return (
    <div className="telemetry-card h-full flex flex-col justify-between">
      <div className="widget-header">
        <span className="glow-dot cyan"></span>
        <span className="widget-title">COGNITIVE PROCESSOR STATE</span>
      </div>
      
      <div className="relative flex items-center justify-center h-48 my-4">
        {/* Core Node */}
        <div className="relative z-10 w-16 h-16 rounded-full bg-gradient-to-br from-cyan-400 to-purple-600 flex items-center justify-center shadow-lg shadow-cyan-500/30">
          <Brain className="text-white" size={28} />
          {/* Neural Pulse Waves */}
          {pulses.map(pulse => (
            <motion.div
              key={pulse.id}
              className="absolute inset-0 rounded-full border border-cyan-400/50"
              initial={{ scale: 1, opacity: 0.8 }}
              animate={{ scale: 3.5, opacity: 0 }}
              transition={{ duration: 2, ease: "easeOut" }}
            />
          ))}
        </div>

        {/* Orbiting Satellite Nodes */}
        <div className="absolute w-36 h-36 border border-dashed border-cyan-500/20 rounded-full animate-[spin_10s_linear_infinite]" />
        <div className="absolute w-44 h-44 border border-dashed border-purple-500/10 rounded-full animate-[spin_20s_linear_infinite_reverse]" />
        
        {/* Connection points */}
        <div className="absolute top-10 left-10 w-3 h-3 rounded-full bg-cyan-400/80 shadow-cyan shadow-sm animate-ping" />
        <div className="absolute bottom-12 right-8 w-2 h-2 rounded-full bg-purple-400/80 shadow-purple shadow-sm animate-pulse" />
        <div className="absolute top-1/2 right-4 w-3.5 h-3.5 rounded-full bg-blue-500/60 shadow-blue shadow-sm" />
      </div>

      <div className="widget-stats text-xs font-mono border-t border-white/5 pt-3">
        <div className="flex justify-between my-1">
          <span className="text-white/40">SMART PATH INTENT:</span>
          <span className="text-cyan-400 font-bold">ROUTING HIGH</span>
        </div>
        <div className="flex justify-between my-1">
          <span className="text-white/40">REASONING LATENCY:</span>
          <span className="text-purple-400">42ms / prompt</span>
        </div>
        <div className="flex justify-between my-1">
          <span className="text-white/40">CORE SYNTHESIS SPEED:</span>
          <span className="text-emerald-400">84.2 tok/s</span>
        </div>
      </div>
    </div>
  );
};

// --- WIDGET 2: AUDIO OSCILLOSCOPE (Voice & Audio) ---
const AudioOscilloscope = ({ isListening, threshold }) => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animationFrameId;
    let phase = 0;

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const width = canvas.width;
      const height = canvas.height;
      const midY = height / 2;

      // Draw grids
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.03)';
      ctx.lineWidth = 1;
      for (let i = 0; i < width; i += 20) {
        ctx.beginPath();
        ctx.moveTo(i, 0);
        ctx.lineTo(i, height);
        ctx.stroke();
      }
      for (let i = 0; i < height; i += 20) {
        ctx.beginPath();
        ctx.moveTo(0, i);
        ctx.lineTo(width, i);
        ctx.stroke();
      }

      // Draw threshold line
      const threshY = midY - (threshold + 60) * 1.5;
      ctx.strokeStyle = 'rgba(239, 68, 68, 0.3)';
      ctx.setLineDash([5, 5]);
      ctx.beginPath();
      ctx.moveTo(0, threshY);
      ctx.lineTo(width, threshY);
      ctx.stroke();
      ctx.setLineDash([]);

      // Draw primary wave
      ctx.beginPath();
      ctx.strokeStyle = 'rgba(43, 205, 255, 0.85)';
      ctx.lineWidth = 2.5;
      ctx.shadowColor = 'rgba(43, 205, 255, 0.5)';
      ctx.shadowBlur = 8;
      
      const amp = isListening ? 25 : 8;
      const freq = isListening ? 0.03 : 0.015;

      for (let x = 0; x < width; x++) {
        const y = midY + Math.sin(x * freq + phase) * amp * Math.sin(x * 0.005) + Math.cos(x * 0.01 - phase * 0.5) * (amp/2);
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();

      // Draw secondary wave
      ctx.shadowBlur = 0;
      ctx.beginPath();
      ctx.strokeStyle = 'rgba(157, 78, 221, 0.4)';
      ctx.lineWidth = 1.5;
      for (let x = 0; x < width; x++) {
        const y = midY + Math.cos(x * (freq * 0.8) - phase) * (amp * 0.7) * Math.sin(x * 0.004);
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();

      phase += isListening ? 0.15 : 0.05;
      animationFrameId = requestAnimationFrame(render);
    };

    render();
    return () => cancelAnimationFrame(animationFrameId);
  }, [isListening, threshold]);

  return (
    <div className="telemetry-card h-full flex flex-col justify-between">
      <div className="widget-header">
        <span className={`glow-dot ${isListening ? 'cyan pulse' : 'yellow'}`}></span>
        <span className="widget-title">AUDIO WAVEFORM SPECTRUM</span>
      </div>
      
      <div className="relative bg-black/40 border border-white/5 rounded-lg overflow-hidden h-40 my-3 flex items-center justify-center">
        <canvas ref={canvasRef} width="300" height="160" className="w-full h-full" />
        <span className="absolute bottom-2 right-3 font-mono text-[9px] text-white/30 tracking-widest">
          SYS_MIC_LIVE: {isListening ? 'STREAMING' : 'IDLE'}
        </span>
      </div>

      <div className="widget-stats text-xs font-mono border-t border-white/5 pt-3">
        <div className="flex justify-between my-1">
          <span className="text-white/40">VAD TRIGGER LEVEL:</span>
          <span className="text-cyan-400 font-bold">{threshold} dB</span>
        </div>
        <div className="flex justify-between my-1">
          <span className="text-white/40">MIC INPUT STATUS:</span>
          <span className="text-emerald-400">ONLINE</span>
        </div>
        <div className="flex justify-between my-1">
          <span className="text-white/40">SAMPLING RATE:</span>
          <span className="text-purple-400">16,000 Hz MONO</span>
        </div>
      </div>
    </div>
  );
};

// --- WIDGET 3: NEURAL MEMORY GRAPH (Memory System) ---
const NeuralMemoryGraph = ({ retentionMode, scale }) => {
  return (
    <div className="telemetry-card h-full flex flex-col justify-between">
      <div className="widget-header">
        <span className="glow-dot purple animate-pulse"></span>
        <span className="widget-title">COGNITIVE KNOWLEDGE STORAGE</span>
      </div>
      
      <div className="relative h-44 my-3 border border-white/5 bg-black/30 rounded-lg overflow-hidden flex flex-col justify-center items-center">
        {/* Animated Scanning Grid */}
        <div className="absolute inset-0 bg-[linear-gradient(to_bottom,rgba(255,255,255,0.01)_1px,transparent_1px),linear-gradient(to_right,rgba(255,255,255,0.01)_1px,transparent_1px)] bg-[size:15px_15px]" />
        
        {/* Radial Memory Network */}
        <svg className="w-40 h-40 z-10" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="3" fill="#2bcdff" className="animate-ping" />
          <circle cx="50" cy="50" r="2" fill="#2bcdff" />
          
          <circle cx="25" cy="30" r="1.5" fill="#9d4edd" />
          <circle cx="75" cy="35" r="1.5" fill="#2bcdff" />
          <circle cx="35" cy="70" r="1.5" fill="#9d4edd" />
          <circle cx="65" cy="75" r="1.5" fill="#2bcdff" />
          <circle cx="50" cy="20" r="1.5" fill="#e2e8f0" />
          
          {/* Paths connecting nodes */}
          <line x1="50" y1="50" x2="25" y2="30" stroke="rgba(157, 78, 221, 0.4)" strokeWidth="0.5" className="animate-pulse" />
          <line x1="50" y1="50" x2="75" y2="35" stroke="rgba(43, 205, 255, 0.4)" strokeWidth="0.5" />
          <line x1="50" y1="50" x2="35" y2="70" stroke="rgba(157, 78, 221, 0.4)" strokeWidth="0.5" />
          <line x1="50" y1="50" x2="65" y2="75" stroke="rgba(43, 205, 255, 0.4)" strokeWidth="0.5" />
          <line x1="25" y1="30" x2="50" y2="20" stroke="rgba(255, 255, 255, 0.2)" strokeWidth="0.5" />
          <line x1="75" y1="35" x2="50" y2="20" stroke="rgba(255, 255, 255, 0.2)" strokeWidth="0.5" />
        </svg>

        <div className="absolute inset-x-0 bottom-2 text-center z-20">
          <div className="text-[10px] text-purple-400 font-mono tracking-widest uppercase">
            RETENTION: {retentionMode}
          </div>
        </div>
      </div>

      <div className="widget-stats text-xs font-mono border-t border-white/5 pt-3">
        <div className="flex justify-between my-1">
          <span className="text-white/40">SEMANTIC VAULT:</span>
          <span className="text-purple-400 font-bold">14,892 Vectors</span>
        </div>
        <div className="flex justify-between my-1">
          <span className="text-white/40">PROCEDURAL SCHEMAS:</span>
          <span className="text-cyan-400 font-bold">142 Workflows</span>
        </div>
        <div className="flex justify-between my-1">
          <span className="text-white/40">RETRACTIVE DECAY SPEED:</span>
          <span className="text-white/70">{(scale * 100).toFixed(0)}% Intensity</span>
        </div>
      </div>
    </div>
  );
};

// --- WIDGET 4: AUTOMATION STEPS LOG (Automation Engine) ---
const AutomationStepsLog = ({ isExecuting, retryDepth }) => {
  const steps = [
    { label: "Compile ReAct workflow instructions", status: "SUCCESS" },
    { label: "Instantiate persistent Chromium context", status: "SUCCESS" },
    { label: "Synchronize DOM selectors to local cache", status: "SUCCESS" },
    { label: "Execute browser navigation to workspace link", status: "SUCCESS" },
    { label: "Fill elements & locate click targets", status: "RUNNING" },
    { label: "Observe action result & build validation telemetry", status: "PENDING" }
  ];

  return (
    <div className="telemetry-card h-full flex flex-col justify-between">
      <div className="widget-header">
        <span className="glow-dot yellow animate-ping"></span>
        <span className="widget-title">RUNNING ORCHESTRATION PIPELINE</span>
      </div>

      <div className="automation-pipeline my-3 bg-black/40 border border-white/5 rounded-lg p-3 font-mono text-[10px] h-48 overflow-y-auto custom-scrollbar flex flex-col gap-2">
        {steps.map((step, i) => (
          <div key={i} className="flex gap-2 items-start">
            <span className={`w-3.5 h-3.5 rounded-full flex items-center justify-center font-bold text-[8px] mt-0.5 shrink-0 ${
              step.status === 'SUCCESS' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' :
              step.status === 'RUNNING' ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40 animate-pulse' :
              'bg-white/5 text-white/30 border border-white/10'
            }`}>
              {step.status === 'SUCCESS' ? '✓' : step.status === 'RUNNING' ? '▶' : '○'}
            </span>
            <div className="flex-1">
              <p className={step.status === 'SUCCESS' ? 'text-white/70' : step.status === 'RUNNING' ? 'text-cyan-400 font-bold' : 'text-white/30'}>
                {step.label}
              </p>
              {step.status === 'RUNNING' && (
                <div className="w-full bg-white/5 h-1 rounded overflow-hidden mt-1">
                  <div className="h-full bg-cyan-400 animate-[loading_2s_infinite]" style={{ width: '40%' }} />
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="widget-stats text-xs font-mono border-t border-white/5 pt-3">
        <div className="flex justify-between my-1">
          <span className="text-white/40">RETRIES LIMIT:</span>
          <span className="text-yellow-400 font-bold">{retryDepth} Max Retries</span>
        </div>
        <div className="flex justify-between my-1">
          <span className="text-white/40">PLAYWRIGHT ENGINE:</span>
          <span className="text-emerald-400">PERSISTENT CONTEXT</span>
        </div>
      </div>
    </div>
  );
};

// --- WIDGET 5: LAYOUT MONITOR SCANNER (Visual Cognition) ---
const LayoutMonitorScanner = ({ ocr, layout }) => {
  return (
    <div className="telemetry-card h-full flex flex-col justify-between">
      <div className="widget-header">
        <span className="glow-dot cyan"></span>
        <span className="widget-title">VISION LAYER SEGMENTATION</span>
      </div>

      <div className="relative my-3 bg-black/40 border border-white/5 rounded-lg overflow-hidden h-40 flex items-center justify-center">
        {/* Grid outline simulation of UI layout */}
        <div className="absolute inset-4 border border-dashed border-cyan-500/20 rounded flex flex-col justify-between p-2">
          {/* Mock Browser Layout */}
          <div className="w-full h-5 border border-white/10 rounded flex justify-between items-center px-2 bg-white/5">
            <div className="w-16 h-2 bg-white/20 rounded" />
            <div className="flex gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-red-500/70" />
              <span className="w-1.5 h-1.5 rounded-full bg-yellow-500/70" />
              <span className="w-1.5 h-1.5 rounded-full bg-green-500/70" />
            </div>
          </div>
          <div className="flex gap-2 flex-1 mt-2">
            <div className="w-1/3 border border-purple-500/30 rounded p-1 bg-purple-500/5 flex flex-col justify-around">
              <div className="w-full h-2 bg-purple-400/20 rounded" />
              <div className="w-8/12 h-2 bg-purple-400/20 rounded" />
            </div>
            <div className="flex-1 border border-cyan-500/30 rounded p-2 bg-cyan-500/5 relative flex flex-col justify-between">
              <div className="w-full h-8 border border-emerald-500/40 rounded flex items-center justify-center text-[8px] font-mono text-emerald-400 bg-emerald-500/5">
                {ocr ? 'OCR ELEMENT MAPPED' : 'OCR DISABLED'}
              </div>
              <div className="w-10 h-2 bg-cyan-400/30 rounded self-end" />
            </div>
          </div>
        </div>

        {/* Scan Line effect */}
        <div className="absolute inset-x-0 w-full h-[2px] bg-cyan-400 shadow-lg shadow-cyan-400/80 animate-[scan_3s_linear_infinite]" />
      </div>

      <div className="widget-stats text-xs font-mono border-t border-white/5 pt-3">
        <div className="flex justify-between my-1">
          <span className="text-white/40">RESOLUTION MODE:</span>
          <span className="text-purple-400 font-bold">{layout ? 'LAYOUT ANALYST' : 'BASIC COORDINATES'}</span>
        </div>
        <div className="flex justify-between my-1">
          <span className="text-white/40">CAPTCHA SOLVER:</span>
          <span className="text-cyan-400">RE-ROUTE ON CAPTCHA</span>
        </div>
      </div>
    </div>
  );
};

// --- WIDGET 6: HEALING ACTION TIMELINE (Recovery & Self-Healing) ---
const HealingTimeline = ({ depth, replanSpeed }) => {
  const recoveryLog = [
    { time: "18:24:02", msg: "AppLaunchError: Settings not registered", type: "error" },
    { time: "18:24:03", msg: "Scanning alternative executable paths...", type: "info" },
    { time: "18:24:04", msg: "Rerouting: Attempt local command fallback", type: "info" },
    { time: "18:24:06", msg: "System auto-repaired. Core state saved.", type: "success" }
  ];

  return (
    <div className="telemetry-card h-full flex flex-col justify-between">
      <div className="widget-header">
        <span className="glow-dot emerald"></span>
        <span className="widget-title">RECOVERY ENGINE TIMELINE</span>
      </div>

      <div className="my-3 bg-black/40 border border-white/5 rounded-lg p-3 font-mono text-[9px] h-40 overflow-y-auto custom-scrollbar flex flex-col gap-2">
        {recoveryLog.map((log, i) => (
          <div key={i} className="flex gap-2">
            <span className="text-white/30 shrink-0">{log.time}</span>
            <span className={
              log.type === 'error' ? 'text-rose-500 font-bold' :
              log.type === 'success' ? 'text-emerald-400 font-bold' :
              'text-cyan-400'
            }>
              [{log.type.toUpperCase()}]
            </span>
            <span className="text-white/80">{log.msg}</span>
          </div>
        ))}
      </div>

      <div className="widget-stats text-xs font-mono border-t border-white/5 pt-3">
        <div className="flex justify-between my-1">
          <span className="text-white/40">HEALING DEPTH LEVEL:</span>
          <span className="text-cyan-400 font-bold">{depth} Levels</span>
        </div>
        <div className="flex justify-between my-1">
          <span className="text-white/40">REPLAN AGGRESSION:</span>
          <span className="text-purple-400 font-bold">{replanSpeed}</span>
        </div>
        <div className="flex justify-between my-1">
          <span className="text-white/40">HEALING INDEX RATE:</span>
          <span className="text-emerald-400">99.1% SUCCESS</span>
        </div>
      </div>
    </div>
  );
};

// --- WIDGET 7: TOOL PIPELINE (Dynamic Tool Synthesis) ---
const ToolPipeline = ({ validation }) => {
  return (
    <div className="telemetry-card h-full flex flex-col justify-between">
      <div className="widget-header">
        <span className="glow-dot purple"></span>
        <span className="widget-title">DYNAMIC TOOL SYNTHESIS CHAIN</span>
      </div>

      <div className="my-3 flex items-center justify-between px-2 py-4 bg-black/40 border border-white/5 rounded-lg h-40 relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(157,78,221,0.05),transparent_70%)]" />
        
        {/* Pipeline Nodes */}
        <div className="flex flex-col items-center z-10 w-1/4">
          <div className="w-10 h-10 rounded bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400 animate-pulse">
            <Code size={18} />
          </div>
          <span className="text-[8px] font-mono text-white/50 mt-1 uppercase">Synthesis</span>
        </div>

        <ChevronRight size={14} className="text-white/20 animate-pulse" />

        <div className="flex flex-col items-center z-10 w-1/4">
          <div className="w-10 h-10 rounded bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <Terminal size={18} />
          </div>
          <span className="text-[8px] font-mono text-white/50 mt-1 uppercase">Sandbox Compile</span>
        </div>

        <ChevronRight size={14} className="text-white/20" />

        <div className="flex flex-col items-center z-10 w-1/4">
          <div className="w-10 h-10 rounded bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <Check size={18} />
          </div>
          <span className="text-[8px] font-mono text-white/50 mt-1 uppercase">Validation: {validation}</span>
        </div>
      </div>

      <div className="widget-stats text-xs font-mono border-t border-white/5 pt-3">
        <div className="flex justify-between my-1">
          <span className="text-white/40">TEMPORARY RUNTIME TOOLS:</span>
          <span className="text-purple-400 font-bold">12 Compile Active</span>
        </div>
        <div className="flex justify-between my-1">
          <span className="text-white/40">COMPILATION SUCCESS:</span>
          <span className="text-emerald-400">97.8%</span>
        </div>
      </div>
    </div>
  );
};

// --- WIDGET 8: BIOMETRIC SCANNER (Security & Privacy) ---
const BiometricScanner = ({ activeScan }) => {
  return (
    <div className="telemetry-card h-full flex flex-col justify-between">
      <div className="widget-header">
        <span className="glow-dot rose"></span>
        <span className="widget-title">BIOMETRIC VAULT CRYPTO LOCK</span>
      </div>

      <div className="relative my-3 bg-black/40 border border-white/5 rounded-lg overflow-hidden h-40 flex items-center justify-center">
        {/* Concentric rotating circles */}
        <div className="absolute w-28 h-28 border border-dashed border-rose-500/30 rounded-full animate-[spin_12s_linear_infinite]" />
        <div className="absolute w-24 h-24 border border-rose-500/20 rounded-full flex items-center justify-center">
          <div className="w-16 h-16 border-2 border-double border-rose-500/40 rounded-full flex items-center justify-center bg-rose-500/5">
            {activeScan ? (
              <Lock className="text-rose-400 animate-pulse" size={24} />
            ) : (
              <Shield className="text-rose-400" size={24} />
            )}
          </div>
        </div>
        {/* Reticles */}
        <div className="absolute w-32 h-32 border-l border-t border-rose-500/50 top-4 left-24 w-4 h-4" />
        <div className="absolute w-32 h-32 border-r border-t border-rose-500/50 top-4 right-24 w-4 h-4" />
        <div className="absolute w-32 h-32 border-l border-b border-rose-500/50 bottom-4 left-24 w-4 h-4" />
        <div className="absolute w-32 h-32 border-r border-b border-rose-500/50 bottom-4 right-24 w-4 h-4" />
        
        {/* Scanning horizontal red light */}
        <div className="absolute inset-x-0 w-full h-[1px] bg-rose-500 shadow-md shadow-rose-500 animate-[scan_4s_ease-in-out_infinite]" />
      </div>

      <div className="widget-stats text-xs font-mono border-t border-white/5 pt-3">
        <div className="flex justify-between my-1">
          <span className="text-white/40">SHA-256 VAULT STATUS:</span>
          <span className="text-rose-500 font-bold">SECURED & ENCRYPTED</span>
        </div>
        <div className="flex justify-between my-1">
          <span className="text-white/40">AUTHENTICATION LAYERS:</span>
          <span className="text-white/70">Biometric & Secret Tokens</span>
        </div>
      </div>
    </div>
  );
};

// --- WIDGET 9: REALTIME HARDWARE PLOT (Performance) ---
const RealtimeHardwarePlot = () => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let frameId;
    let points = Array(30).fill(0).map(() => ({
      cpu: Math.random() * 40 + 20,
      gpu: Math.random() * 30 + 10,
      ram: 58
    }));

    const updatePoints = () => {
      points.shift();
      points.push({
        cpu: Math.max(10, Math.min(100, points[points.length - 1].cpu + (Math.random() - 0.5) * 12)),
        gpu: Math.max(5, Math.min(100, points[points.length - 1].gpu + (Math.random() - 0.5) * 8)),
        ram: Math.max(50, Math.min(70, points[points.length - 1].ram + (Math.random() - 0.5) * 1))
      });
    };

    const interval = setInterval(updatePoints, 300);

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const width = canvas.width;
      const height = canvas.height;
      const step = width / (points.length - 1);

      // Draw grids
      ctx.strokeStyle = 'rgba(255,255,255,0.02)';
      ctx.lineWidth = 1;
      for (let i = 0; i < width; i += 30) {
        ctx.beginPath();
        ctx.moveTo(i, 0);
        ctx.lineTo(i, height);
        ctx.stroke();
      }
      for (let i = 0; i < height; i += 20) {
        ctx.beginPath();
        ctx.moveTo(0, i);
        ctx.lineTo(width, i);
        ctx.stroke();
      }

      // Plot helper
      const plotLine = (key, strokeColor, fillColor) => {
        ctx.beginPath();
        points.forEach((pt, idx) => {
          const x = idx * step;
          const y = height - (pt[key] / 100) * (height - 10) - 5;
          if (idx === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        });
        ctx.strokeStyle = strokeColor;
        ctx.lineWidth = 2;
        ctx.stroke();

        // Fill area
        ctx.lineTo(width, height);
        ctx.lineTo(0, height);
        ctx.fillStyle = fillColor;
        ctx.fill();
      };

      plotLine('ram', 'rgba(157, 78, 221, 0.6)', 'rgba(157, 78, 221, 0.05)');
      plotLine('gpu', 'rgba(16, 185, 129, 0.6)', 'rgba(16, 185, 129, 0.05)');
      plotLine('cpu', 'rgba(43, 205, 255, 0.8)', 'rgba(43, 205, 255, 0.05)');

      frameId = requestAnimationFrame(render);
    };

    render();
    return () => {
      clearInterval(interval);
      cancelAnimationFrame(frameId);
    };
  }, []);

  return (
    <div className="telemetry-card h-full flex flex-col justify-between">
      <div className="widget-header">
        <span className="glow-dot cyan"></span>
        <span className="widget-title">HARDWARE TELEMETRY HUD</span>
      </div>

      <div className="relative bg-black/40 border border-white/5 rounded-lg overflow-hidden h-36 my-2">
        <canvas ref={canvasRef} width="300" height="144" className="w-full h-full" />
        {/* Colors key labels */}
        <div className="absolute top-2 left-3 flex gap-3 text-[8px] font-mono">
          <span className="text-cyan-400">● CPU</span>
          <span className="text-emerald-400">● GPU</span>
          <span className="text-purple-400">● RAM</span>
        </div>
      </div>

      <div className="widget-stats text-xs font-mono border-t border-white/5 pt-3">
        <div className="flex justify-between my-1">
          <span className="text-white/40">CPU CORE ASSIGN:</span>
          <span className="text-cyan-400 font-bold">8 Threads (Active)</span>
        </div>
        <div className="flex justify-between my-1">
          <span className="text-white/40">ORCHESTRATION LOAD:</span>
          <span className="text-purple-400">24.5% Active</span>
        </div>
      </div>
    </div>
  );
};

// --- WIDGET 10: INTEGRATION MATRIX (Integrations) ---
const IntegrationMatrix = () => {
  const pings = [
    { name: "Google API", ping: "42ms", health: "100%" },
    { name: "Spotify API", ping: "12ms", health: "100%" },
    { name: "GitHub Hooks", ping: "35ms", health: "98.9%" },
    { name: "Discord API", ping: "58ms", health: "100%" },
    { name: "Groq Cloud LPU", ping: "89ms", health: "99.9%" }
  ];

  return (
    <div className="telemetry-card h-full flex flex-col justify-between">
      <div className="widget-header">
        <span className="glow-dot cyan"></span>
        <span className="widget-title">CONNECTION HEALTH MATRIX</span>
      </div>

      <div className="my-3 bg-black/40 border border-white/5 rounded-lg p-3 font-mono text-[9px] flex flex-col gap-2 h-40 justify-center">
        {pings.map((service, i) => (
          <div key={i} className="flex justify-between items-center border-b border-white/5 pb-1">
            <span className="text-white/80">{service.name}</span>
            <div className="flex gap-3">
              <span className="text-cyan-400">{service.ping}</span>
              <span className="text-emerald-400 font-bold">{service.health}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="widget-stats text-xs font-mono border-t border-white/5 pt-3">
        <div className="flex justify-between my-1">
          <span className="text-white/40">GATEWAY SYNC PROTOCOL:</span>
          <span className="text-purple-400">WebSocket Live Secure</span>
        </div>
      </div>
    </div>
  );
};

// --- WIDGET 11: DEVELOPER TERMINAL (Developer Console) ---
const DeveloperTerminal = () => {
  const [logs, setLogs] = useState([
    "NOVA_OS: Init boot process complete.",
    "AGENT_CORE: Loading Dynamic Tool Registry... discovered 32 tools.",
    "NLP_ROUTER: Pipeline route set to smart SMART_PATH.",
    "NEURAL_ENGINE: Connected to Groq LLaMA 3.3 API. Latency optimal."
  ]);
  const [inputValue, setInputValue] = useState("");
  const terminalEndRef = useRef(null);

  const mockCommands = {
    '/help': [
      "Available commands:",
      "  /status  - Inspect subsystems and core temperature.",
      "  /agent   - View active ReAct orchestration parameters.",
      "  /clear   - Clear terminal logs."
    ],
    '/status': [
      "SYS STATUS: Core systems operational.",
      "  - Cognitive Load: 12% | Temperature: 42°C",
      "  - Memory Vector Index: 14,892 Vectors",
      "  - Running Agents: 1 Swarm Orchestrator"
    ],
    '/agent': [
      "ACTIVE AGENTS REGISTRY:",
      "  - Swarm Controller: Operational (10 iter max)",
      "  - Tools Synthesizer: Standby",
      "  - Recovery Daemon: Active [Retry Count: 3]"
    ]
  };

  const handleCommandSubmit = (e) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const cmd = inputValue.trim();
    setLogs(prev => [...prev, `NOVA_CLI_GUEST$ ${cmd}`]);

    setTimeout(() => {
      if (cmd === '/clear') {
        setLogs([]);
      } else if (mockCommands[cmd]) {
        setLogs(prev => [...prev, ...mockCommands[cmd]]);
      } else {
        setLogs(prev => [...prev, `ERR: Command '${cmd}' not recognized. Type /help for options.`]);
      }
    }, 100);

    setInputValue("");
  };

  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  // Periodic random logs to simulate activity
  useEffect(() => {
    const randomLogs = [
      "AGENT_ORCHESTRATOR: Thinking... parsed goal tag.",
      "PROCEDURAL_MEMORY: Workflow task registered successfully.",
      "BROWSER_CONTROLLER: Playwright session optimized.",
      "METAEVALUATOR: Execution logs parsed; 0 anomalies detected."
    ];

    const interval = setInterval(() => {
      setLogs(prev => [...prev, `SYS_MONITOR: ${randomLogs[Math.floor(Math.random() * randomLogs.length)]}`].slice(-40));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="telemetry-card h-full flex flex-col justify-between">
      <div className="widget-header">
        <span className="glow-dot cyan"></span>
        <span className="widget-title">AGENT RUNTIME INTERACTIVE CLI</span>
      </div>

      <div className="relative my-3 flex-1 flex flex-col bg-black border border-white/10 rounded-lg p-3 font-mono text-[9px] h-64">
        <div className="flex-1 overflow-y-auto custom-scrollbar flex flex-col gap-1 select-text">
          {logs.map((log, idx) => (
            <div key={idx} className={
              log.startsWith('NOVA_CLI') ? 'text-cyan-400 font-bold' :
              log.startsWith('ERR:') ? 'text-rose-500' :
              log.startsWith('SYS_MONITOR:') ? 'text-purple-400/80' :
              'text-white/70'
            }>
              {log}
            </div>
          ))}
          <div ref={terminalEndRef} />
        </div>

        <form onSubmit={handleCommandSubmit} className="flex border-t border-white/10 pt-2 mt-2">
          <span className="text-cyan-400 mr-1 select-none">NOVA_CLI_GUEST$</span>
          <input
            type="text"
            className="flex-1 bg-transparent border-none outline-none text-white font-mono p-0 m-0"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Type /help..."
          />
        </form>
      </div>

      <span className="text-[8px] font-mono text-white/30 uppercase text-right block">Console v2.0 - Active Stream</span>
    </div>
  );
};

// --- WIDGET 12: QUANTUM PROJECTION CHIP (Experimental Features) ---
const QuantumProjectionChip = () => {
  return (
    <div className="telemetry-card h-full flex flex-col justify-between">
      <div className="widget-header">
        <span className="glow-dot amber animate-pulse"></span>
        <span className="widget-title">QUANTUM META-COGNITIVE LAYER</span>
      </div>

      <div className="relative my-3 bg-black/40 border border-white/5 rounded-lg overflow-hidden h-44 flex flex-col items-center justify-center">
        {/* Danger background overlay */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(245,158,11,0.05),transparent_70%)]" />
        
        {/* Animated Rotating SVG Wireframe */}
        <svg className="w-28 h-28 z-10 animate-[spin_15s_linear_infinite]" viewBox="0 0 100 100">
          <polygon points="50,10 90,30 90,70 50,90 10,70 10,30" fill="none" stroke="rgba(245, 158, 11, 0.4)" strokeWidth="1" />
          <polygon points="50,20 80,35 80,65 50,80 20,65 20,35" fill="none" stroke="rgba(43, 205, 255, 0.3)" strokeWidth="0.8" />
          <line x1="50" y1="10" x2="50" y2="90" stroke="rgba(245, 158, 11, 0.15)" strokeWidth="0.5" />
          <line x1="10" y1="30" x2="90" y2="70" stroke="rgba(245, 158, 11, 0.15)" strokeWidth="0.5" />
          <line x1="90" y1="30" x2="10" y2="70" stroke="rgba(245, 158, 11, 0.15)" strokeWidth="0.5" />
          <circle cx="50" cy="50" r="8" fill="none" stroke="#f59e0b" strokeWidth="1.5" className="animate-pulse" />
        </svg>

        <div className="absolute bottom-2 font-mono text-[9px] text-amber-500/70 tracking-widest text-center px-4 uppercase select-none">
          ☢ WARNING: EXPERIMENTAL CORE ACTIVE
        </div>
      </div>

      <div className="widget-stats text-xs font-mono border-t border-white/5 pt-3">
        <div className="flex justify-between my-1">
          <span className="text-white/40">META-SWARM SYNAPSE:</span>
          <span className="text-amber-500 font-bold">UNSTABLE CORE</span>
        </div>
      </div>
    </div>
  );
};


// --- MAIN SETTINGS PAGE COMPONENT ---
const SettingsPage = () => {
  const [activeTab, setActiveTab] = useState('ai_core');
  const [showToast, setShowToast] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  
  // 1. AI Core States
  const [aiModel, setAiModel] = useState(() => localStorage.getItem('nova_setting_ai_model') || 'LLaMA 3.3 70B (Default)');
  const [autonomousMode, setAutonomousMode] = useState(() => localStorage.getItem('nova_setting_autonomous_mode') !== 'false');
  const [reasoningDepth, setReasoningDepth] = useState(() => localStorage.getItem('nova_setting_reasoning_depth') || 'Deep');
  const [planningComplexity, setPlanningComplexity] = useState(() => localStorage.getItem('nova_setting_planning_complexity') || 'Hierarchical');
  const [cognitiveTemp, setCognitiveTemp] = useState(() => parseFloat(localStorage.getItem('nova_setting_cognitive_temp') || '0.5'));
  const [multiAgentMode, setMultiAgentMode] = useState(() => localStorage.getItem('nova_setting_multi_agent_mode') !== 'false');
  const [proceduralLearning, setProceduralLearning] = useState(() => localStorage.getItem('nova_setting_procedural_learning') !== 'false');

  // 2. Voice States
  const [wakeWord, setWakeWord] = useState(() => localStorage.getItem('nova_setting_wake_word') || 'Hello Nova');
  const [voicePersonality, setVoicePersonality] = useState(() => localStorage.getItem('nova_setting_voice_personality') || 'Cybernetic');
  const [speechSpeed, setSpeechSpeed] = useState(() => parseFloat(localStorage.getItem('nova_setting_speech_speed') || '1.0'));
  const [noiseCancellation, setNoiseCancellation] = useState(() => localStorage.getItem('nova_setting_noise_cancellation') !== 'false');
  const [continuousListening, setContinuousListening] = useState(() => localStorage.getItem('nova_setting_continuous_listening') === 'true');
  const [voiceThreshold, setVoiceThreshold] = useState(() => parseInt(localStorage.getItem('nova_setting_voice_threshold') || '-45', 10));

  // 3. Memory States
  const [workflowLearning, setWorkflowLearning] = useState(() => localStorage.getItem('nova_setting_workflow_learning') !== 'false');
  const [memoryRetention, setMemoryRetention] = useState(() => localStorage.getItem('nova_setting_memory_retention') || 'Adaptive Decay');
  const [learningStrength, setLearningStrength] = useState(() => parseFloat(localStorage.getItem('nova_setting_learning_strength') || '0.85'));

  // 4. Automation States
  const [executionAutonomy, setExecutionAutonomy] = useState(() => localStorage.getItem('nova_setting_execution_autonomy') || 'Suggest (Ask for confirmation)');
  const [browserAutomation, setBrowserAutomation] = useState(() => localStorage.getItem('nova_setting_browser_automation') !== 'false');
  const [desktopAutomation, setDesktopAutomation] = useState(() => localStorage.getItem('nova_setting_desktop_automation') !== 'false');
  const [dynamicWorkflow, setDynamicWorkflow] = useState(() => localStorage.getItem('nova_setting_dynamic_workflow') !== 'false');
  const [autoRecovery, setAutoRecovery] = useState(() => localStorage.getItem('nova_setting_auto_recovery') !== 'false');
  const [retryDepth, setRetryDepth] = useState(() => parseInt(localStorage.getItem('nova_setting_retry_depth') || '3', 10));
  const [visualFallback, setVisualFallback] = useState(() => localStorage.getItem('nova_setting_visual_fallback') !== 'false');

  // 5. Visual Cognition
  const [visualReasoning, setVisualReasoning] = useState(() => localStorage.getItem('nova_setting_visual_reasoning') !== 'false');
  const [ocrEngine, setOcrEngine] = useState(() => localStorage.getItem('nova_setting_ocr_engine') !== 'false');
  const [screenshotAnalysis, setScreenshotAnalysis] = useState(() => localStorage.getItem('nova_setting_screenshot_analysis') !== 'false');
  const [layoutUnderstanding, setLayoutUnderstanding] = useState(() => localStorage.getItem('nova_setting_layout_understanding') !== 'false');
  const [interfaceMemory, setInterfaceMemory] = useState(() => localStorage.getItem('nova_setting_interface_memory') !== 'false');
  const [captchaDetection, setCaptchaDetection] = useState(() => localStorage.getItem('nova_setting_captcha_detection') !== 'false');

  // 6. Recovery & Self-Healing
  const [adaptiveRecovery, setAdaptiveRecovery] = useState(() => localStorage.getItem('nova_setting_adaptive_recovery') !== 'false');
  const [replanningAggressiveness, setReplanningAggressiveness] = useState(() => localStorage.getItem('nova_setting_replanning_aggressiveness') || 'Moderate');
  const [selfHealingDepth, setSelfHealingDepth] = useState(() => parseInt(localStorage.getItem('nova_setting_self_healing_depth') || '5', 10));
  const [fallbackStrategy, setFallbackStrategy] = useState(() => localStorage.getItem('nova_setting_fallback_strategy') || 'Replan Task');
  const [anomalyDetection, setAnomalyDetection] = useState(() => localStorage.getItem('nova_setting_anomaly_detection') !== 'false');

  // 7. Dynamic Tool Synthesis
  const [toolSynthesis, setToolSynthesis] = useState(() => localStorage.getItem('nova_setting_tool_synthesis') !== 'false');
  const [validationStrictness, setValidationStrictness] = useState(() => localStorage.getItem('nova_setting_validation_strictness') || 'Medium');
  const [autoApproveTools, setAutoApproveTools] = useState(() => localStorage.getItem('nova_setting_auto_approve_tools') !== 'false');

  // 8. Security & Privacy
  const [faceAuth, setFaceAuth] = useState(() => localStorage.getItem('nova_setting_face_auth') !== 'false');
  const [voiceAuth, setVoiceAuth] = useState(() => localStorage.getItem('nova_setting_voice_auth') !== 'false');
  const [secureMemoryVault, setSecureMemoryVault] = useState(() => localStorage.getItem('nova_setting_secure_vault') !== 'false');
  const [encryptedStorage, setEncryptedStorage] = useState(() => localStorage.getItem('nova_setting_encrypted_storage') !== 'false');
  const [apiKeyManager, setApiKeyManager] = useState(() => localStorage.getItem('nova_setting_api_key') || '••••••••••••••••••••••••');
  const [localOnlyMode, setLocalOnlyMode] = useState(() => localStorage.getItem('nova_setting_local_only') === 'true');

  // 9. Performance & Optimization
  const [energyMode, setEnergyMode] = useState(() => localStorage.getItem('nova_setting_energy_mode') || 'Balanced');
  const [animationIntensity, setAnimationIntensity] = useState(() => parseInt(localStorage.getItem('nova_setting_animation_intensity') || '80', 10));
  const [backgroundProcessing, setBackgroundProcessing] = useState(() => localStorage.getItem('nova_setting_background_processing') !== 'false');
  const [cacheAutoPurge, setCacheAutoPurge] = useState(() => localStorage.getItem('nova_setting_cache_auto_purge') !== 'false');

  // 10. Connected Integrations (Status state only)
  const [integrationsState, setIntegrationsState] = useState({
    spotify: true,
    google: false,
    github: true,
    discord: true,
    gmail: false,
    notion: false,
    calendar: true,
    mongodb: true,
    groq: true
  });

  // 12. Experimental Features
  const [multiAgentSwarm, setMultiAgentSwarm] = useState(() => localStorage.getItem('nova_setting_swarm') === 'true');
  const [metaCognition, setMetaCognition] = useState(() => localStorage.getItem('nova_setting_meta_cognition') === 'true');
  const [predictivePlanning, setPredictivePlanning] = useState(() => localStorage.getItem('nova_setting_predictive_planning') === 'true');
  const [selfEvolvingArch, setSelfEvolvingArch] = useState(() => localStorage.getItem('nova_setting_self_evolving') === 'true');
  const [dynamicCompression, setDynamicCompression] = useState(() => localStorage.getItem('nova_setting_tool_compression') === 'true');
  const [experimentalVision, setExperimentalVision] = useState(() => localStorage.getItem('nova_setting_exp_vision') === 'true');

  const tabs = [
    { id: 'ai_core', icon: <Brain size={18}/>, label: 'AI Core' },
    { id: 'voice_audio', icon: <Mic size={18}/>, label: 'Voice & Audio' },
    { id: 'memory_system', icon: <Cpu size={18}/>, label: 'Memory System' },
    { id: 'automation_engine', icon: <Zap size={18}/>, label: 'Automation Engine' },
    { id: 'visual_cognition', icon: <Eye size={18}/>, label: 'Visual Cognition' },
    { id: 'recovery_healing', icon: <HeartPulse size={18}/>, label: 'Recovery & Self-Healing' },
    { id: 'tool_synthesis', icon: <Wrench size={18}/>, label: 'Dynamic Tool Synthesis' },
    { id: 'security_privacy', icon: <Shield size={18}/>, label: 'Security & Privacy' },
    { id: 'performance_opt', icon: <Gauge size={18}/>, label: 'Performance & Opt.' },
    { id: 'integrations', icon: <Link size={18}/>, label: 'Integrations' },
    { id: 'developer_console', icon: <Terminal size={18}/>, label: 'Developer Console' },
    { id: 'experimental_features', icon: <Flame size={18}/>, label: 'Experimental' }
  ];

  const handleSave = async () => {
    // Save all current parameters to local storage
    localStorage.setItem('nova_setting_ai_model', aiModel);
    localStorage.setItem('nova_setting_autonomous_mode', autonomousMode.toString());
    localStorage.setItem('nova_setting_reasoning_depth', reasoningDepth);
    localStorage.setItem('nova_setting_planning_complexity', planningComplexity);
    localStorage.setItem('nova_setting_cognitive_temp', cognitiveTemp.toString());
    localStorage.setItem('nova_setting_multi_agent_mode', multiAgentMode.toString());
    localStorage.setItem('nova_setting_procedural_learning', proceduralLearning.toString());

    localStorage.setItem('nova_setting_wake_word', wakeWord);
    localStorage.setItem('nova_setting_voice_personality', voicePersonality);
    localStorage.setItem('nova_setting_speech_speed', speechSpeed.toString());
    localStorage.setItem('nova_setting_noise_cancellation', noiseCancellation.toString());
    localStorage.setItem('nova_setting_continuous_listening', continuousListening.toString());
    localStorage.setItem('nova_setting_voice_threshold', voiceThreshold.toString());

    localStorage.setItem('nova_setting_workflow_learning', workflowLearning.toString());
    localStorage.setItem('nova_setting_memory_retention', memoryRetention);
    localStorage.setItem('nova_setting_learning_strength', learningStrength.toString());

    localStorage.setItem('nova_setting_execution_autonomy', executionAutonomy);
    localStorage.setItem('nova_setting_browser_automation', browserAutomation.toString());
    localStorage.setItem('nova_setting_desktop_automation', desktopAutomation.toString());
    localStorage.setItem('nova_setting_dynamic_workflow', dynamicWorkflow.toString());
    localStorage.setItem('nova_setting_auto_recovery', autoRecovery.toString());
    localStorage.setItem('nova_setting_retry_depth', retryDepth.toString());
    localStorage.setItem('nova_setting_visual_fallback', visualFallback.toString());

    localStorage.setItem('nova_setting_visual_reasoning', visualReasoning.toString());
    localStorage.setItem('nova_setting_ocr_engine', ocrEngine.toString());
    localStorage.setItem('nova_setting_screenshot_analysis', screenshotAnalysis.toString());
    localStorage.setItem('nova_setting_layout_understanding', layoutUnderstanding.toString());
    localStorage.setItem('nova_setting_interface_memory', interfaceMemory.toString());
    localStorage.setItem('nova_setting_captcha_detection', captchaDetection.toString());

    localStorage.setItem('nova_setting_adaptive_recovery', adaptiveRecovery.toString());
    localStorage.setItem('nova_setting_replanning_aggressiveness', replanningAggressiveness);
    localStorage.setItem('nova_setting_self_healing_depth', selfHealingDepth.toString());
    localStorage.setItem('nova_setting_fallback_strategy', fallbackStrategy);
    localStorage.setItem('nova_setting_anomaly_detection', anomalyDetection.toString());

    localStorage.setItem('nova_setting_tool_synthesis', toolSynthesis.toString());
    localStorage.setItem('nova_setting_validation_strictness', validationStrictness);
    localStorage.setItem('nova_setting_auto_approve_tools', autoApproveTools.toString());

    localStorage.setItem('nova_setting_face_auth', faceAuth.toString());
    localStorage.setItem('nova_setting_voice_auth', voiceAuth.toString());
    localStorage.setItem('nova_setting_secure_vault', secureMemoryVault.toString());
    localStorage.setItem('nova_setting_encrypted_storage', encryptedStorage.toString());
    localStorage.setItem('nova_setting_api_key', apiKeyManager);
    localStorage.setItem('nova_setting_local_only', localOnlyMode.toString());

    localStorage.setItem('nova_setting_energy_mode', energyMode);
    localStorage.setItem('nova_setting_animation_intensity', animationIntensity.toString());
    localStorage.setItem('nova_setting_background_processing', backgroundProcessing.toString());
    localStorage.setItem('nova_setting_cache_auto_purge', cacheAutoPurge.toString());

    localStorage.setItem('nova_setting_swarm', multiAgentSwarm.toString());
    localStorage.setItem('nova_setting_meta_cognition', metaCognition.toString());
    localStorage.setItem('nova_setting_predictive_planning', predictivePlanning.toString());
    localStorage.setItem('nova_setting_self_evolving', selfEvolvingArch.toString());
    localStorage.setItem('nova_setting_tool_compression', dynamicCompression.toString());
    localStorage.setItem('nova_setting_exp_vision', experimentalVision.toString());

    // Synchronize to the backend database
    try {
      const activeUser = localStorage.getItem('nova_active_user') || 'amarnath';
      await fetch(`${API_BASE_URL}/auth/preferences`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: activeUser,
          preferences: {
            ai_model: aiModel,
            autonomous_mode: autonomousMode,
            reasoning_depth: reasoningDepth,
            planning_complexity: planningComplexity,
            cognitive_temp: cognitiveTemp,
            multi_agent_mode: multiAgentMode,
            procedural_learning: proceduralLearning,
            wake_word: wakeWord,
            voice_personality: voicePersonality,
            speech_speed: speechSpeed,
            noise_cancellation: noiseCancellation,
            continuous_listening: continuousListening,
            voice_threshold: voiceThreshold,
            workflow_learning: workflowLearning,
            memory_retention: memoryRetention,
            learning_strength: learningStrength,
            execution_autonomy: executionAutonomy,
            browser_automation: browserAutomation,
            desktop_automation: desktopAutomation,
            dynamic_workflow: dynamicWorkflow,
            auto_recovery: autoRecovery,
            retry_depth: retryDepth,
            visual_fallback: visualFallback,
            visual_reasoning: visualReasoning,
            ocr_engine: ocrEngine,
            screenshot_analysis: screenshotAnalysis,
            layout_understanding: layoutUnderstanding,
            interface_memory: interfaceMemory,
            captcha_detection: captchaDetection,
            adaptive_recovery: adaptiveRecovery,
            replanning_aggressiveness: replanningAggressiveness,
            self_healing_depth: selfHealingDepth,
            fallback_strategy: fallbackStrategy,
            anomaly_detection: anomalyDetection,
            tool_synthesis: toolSynthesis,
            validation_strictness: validationStrictness,
            auto_approve_tools: autoApproveTools,
            face_auth: faceAuth,
            voice_auth: voiceAuth,
            secure_vault: secureMemoryVault,
            encrypted_storage: encryptedStorage,
            local_only: localOnlyMode,
            energy_mode: energyMode,
            animation_intensity: animationIntensity,
            background_processing: backgroundProcessing,
            cache_auto_purge: cacheAutoPurge,
            swarm: multiAgentSwarm,
            meta_cognition: metaCognition,
            predictive_planning: predictivePlanning,
            self_evolving: selfEvolvingArch,
            tool_compression: dynamicCompression,
            exp_vision: experimentalVision
          }
        })
      });
    } catch (err) {
      console.error('Failed to sync settings with backend database:', err);
    }

    setShowToast(true);
    setTimeout(() => setShowToast(false), 3000);
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'ai_core':
        return (
          <div className="settings-panel-grid">
            <div className="panel-controls">
              <h2 className="panel-title">AI Core Settings</h2>
              <div className="settings-group">
                <div className="setting-item">
                  <div className="setting-info">
                    <label>AI Model Selector</label>
                    <span>Primary neural engine for intent mapping and chat response.</span>
                  </div>
                  <NeuralDropdown 
                    options={['LLaMA 3.3 70B (Default)', 'DeepSeek R1 (Reasoning)', 'Gemini 1.5 Pro (Multi-modal)', 'GPT-4o (Omni)']}
                    value={aiModel}
                    onChange={setAiModel}
                  />
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Autonomous Execution Mode</label>
                    <span>Allow NOVA to synthesis and resolve capabilities without user prompts.</span>
                  </div>
                  <label className="switch">
                    <input 
                      type="checkbox" 
                      checked={autonomousMode} 
                      onChange={(e) => setAutonomousMode(e.target.checked)} 
                    />
                    <span className="slider round"></span>
                  </label>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Reasoning Depth</label>
                    <span>Configures reasoning loop iterations before compiling final action plan.</span>
                  </div>
                  <div className="segmented-control">
                    {['Low', 'Medium', 'Deep', 'Extreme'].map((depthOption) => (
                      <button 
                        key={depthOption}
                        className={`segmented-btn ${reasoningDepth === depthOption ? 'active' : ''}`}
                        onClick={() => setReasoningDepth(depthOption)}
                      >
                        {depthOption}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Planning Complexity</label>
                    <span>Method utilized to break tasks into executable step sequences.</span>
                  </div>
                  <NeuralDropdown 
                    options={['Linear Flow', 'Hierarchical', 'Multi-agent Adaptive']}
                    value={planningComplexity}
                    onChange={setPlanningComplexity}
                  />
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Cognitive Temperature</label>
                    <span>Lower temp is precise & strict, higher is creative: {cognitiveTemp.toFixed(1)}</span>
                  </div>
                  <input 
                    type="range" 
                    className="setting-range" 
                    min="0.0" 
                    max="1.5" 
                    step="0.1" 
                    value={cognitiveTemp} 
                    onChange={(e) => setCognitiveTemp(parseFloat(e.target.value))} 
                  />
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Multi-Agent Swarm Orchestrator</label>
                    <span>Deploy subordinate specialized agents for complex sub-workflows.</span>
                  </div>
                  <label className="switch">
                    <input 
                      type="checkbox" 
                      checked={multiAgentMode} 
                      onChange={(e) => setMultiAgentMode(e.target.checked)} 
                    />
                    <span className="slider round"></span>
                  </label>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Procedural Memory Learning</label>
                    <span>Learn task-execution shortcuts based on historical outcomes.</span>
                  </div>
                  <label className="switch">
                    <input 
                      type="checkbox" 
                      checked={proceduralLearning} 
                      onChange={(e) => setProceduralLearning(e.target.checked)} 
                    />
                    <span className="slider round"></span>
                  </label>
                </div>
              </div>
            </div>
            
            <div className="panel-telemetry">
              <CognitiveCoreGraph depth={reasoningDepth} temp={cognitiveTemp} />
            </div>
          </div>
        );

      case 'voice_audio':
        return (
          <div className="settings-panel-grid">
            <div className="panel-controls">
              <h2 className="panel-title">Voice & Audio</h2>
              <div className="settings-group">
                <div className="setting-item">
                  <div className="setting-info">
                    <label>Wake Word Settings</label>
                    <span>Keyword to invoke continuous speech recording triggers.</span>
                  </div>
                  <NeuralDropdown 
                    options={['Hello Nova', 'Hey Nova', 'Disabled']}
                    value={wakeWord}
                    onChange={setWakeWord}
                  />
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Voice Persona</label>
                    <span>Vocal synthesis character for Text-to-Speech responses.</span>
                  </div>
                  <NeuralDropdown 
                    options={['Cybernetic', 'Tactical Console', 'Empathic Companion']}
                    value={voicePersonality}
                    onChange={setVoicePersonality}
                  />
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Speech Speed Rate</label>
                    <span>Adjust pace of local speech engine playback: {speechSpeed.toFixed(1)}x</span>
                  </div>
                  <input 
                    type="range" 
                    className="setting-range" 
                    min="0.5" 
                    max="2.0" 
                    step="0.1" 
                    value={speechSpeed} 
                    onChange={(e) => setSpeechSpeed(parseFloat(e.target.value))} 
                  />
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Noise Cancellation Lock</label>
                    <span>Applies a 80Hz bandpass filter to clear ambient background hum.</span>
                  </div>
                  <label className="switch">
                    <input 
                      type="checkbox" 
                      checked={noiseCancellation} 
                      onChange={(e) => setNoiseCancellation(e.target.checked)} 
                    />
                    <span className="slider round"></span>
                  </label>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Continuous Listening Mode</label>
                    <span>Keeps microphone open continuously (Auto-pause during TTS speaking).</span>
                  </div>
                  <label className="switch">
                    <input 
                      type="checkbox" 
                      checked={continuousListening} 
                      onChange={(e) => setContinuousListening(e.target.checked)} 
                    />
                    <span className="slider round"></span>
                  </label>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Voice Activation Threshold</label>
                    <span>Decibel cutoff level to classify vocal commands: {voiceThreshold} dB</span>
                  </div>
                  <input 
                    type="range" 
                    className="setting-range" 
                    min="-60" 
                    max="-10" 
                    step="5" 
                    value={voiceThreshold} 
                    onChange={(e) => setVoiceThreshold(parseInt(e.target.value, 10))} 
                  />
                </div>
              </div>
            </div>

            <div className="panel-telemetry">
              <AudioOscilloscope isListening={continuousListening} threshold={voiceThreshold} />
            </div>
          </div>
        );

      case 'memory_system':
        return (
          <div className="settings-panel-grid">
            <div className="panel-controls">
              <h2 className="panel-title">Memory System</h2>
              <div className="settings-group">
                <div className="setting-item">
                  <div className="setting-info">
                    <label>Workflow Pattern Learning</label>
                    <span>Extract semantic workflow links from custom user action sequences.</span>
                  </div>
                  <label className="switch">
                    <input 
                      type="checkbox" 
                      checked={workflowLearning} 
                      onChange={(e) => setWorkflowLearning(e.target.checked)} 
                    />
                    <span className="slider round"></span>
                  </label>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Memory Retention Strategy</label>
                    <span>Storage decay parameters for retrieved context blocks.</span>
                  </div>
                  <NeuralDropdown 
                    options={['Permanent (Infinite)', 'Session Only (Volatile)', 'Adaptive Decay']}
                    value={memoryRetention}
                    onChange={setMemoryRetention}
                  />
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Adaptive Learning Strength</label>
                    <span>Controls cognitive learning weight updates: {(learningStrength * 100).toFixed(0)}%</span>
                  </div>
                  <input 
                    type="range" 
                    className="setting-range" 
                    min="0.1" 
                    max="1.0" 
                    step="0.05" 
                    value={learningStrength} 
                    onChange={(e) => setLearningStrength(parseFloat(e.target.value))} 
                  />
                </div>

                <div className="setting-item danger border-t border-white/5 pt-6 mt-4">
                  <div className="setting-info">
                    <label className="text-rose-500">Purge Knowledge Bases</label>
                    <span>Permanently erase user profile embeddings and active execution caches.</span>
                  </div>
                  <button className="action-btn danger flex items-center gap-2">
                    <AlertTriangle size={14} /> Purge Memories
                  </button>
                </div>
              </div>
            </div>

            <div className="panel-telemetry">
              <NeuralMemoryGraph retentionMode={memoryRetention} scale={learningStrength} />
            </div>
          </div>
        );

      case 'automation_engine':
        return (
          <div className="settings-panel-grid">
            <div className="panel-controls">
              <h2 className="panel-title">Automation Engine</h2>
              <div className="settings-group">
                <div className="setting-item">
                  <div className="setting-info">
                    <label>Autonomous Execution Level</label>
                    <span>Determine authorization policy for desktop/shell commands.</span>
                  </div>
                  <NeuralDropdown 
                    options={['Strict Authorization', 'Confirm Destructive', 'Full Autonomy']}
                    value={executionAutonomy}
                    onChange={setExecutionAutonomy}
                  />
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Browser Automation (Playwright)</label>
                    <span>Allow agent to interact with browser interfaces and load webpages.</span>
                  </div>
                  <label className="switch">
                    <input 
                      type="checkbox" 
                      checked={browserAutomation} 
                      onChange={(e) => setBrowserAutomation(e.target.checked)} 
                    />
                    <span className="slider round"></span>
                  </label>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Desktop Automation (PyAutoGUI)</label>
                    <span>Allows targeting application windows & simulating desktop cursor events.</span>
                  </div>
                  <label className="switch">
                    <input 
                      type="checkbox" 
                      checked={desktopAutomation} 
                      onChange={(e) => setDesktopAutomation(e.target.checked)} 
                    />
                    <span className="slider round"></span>
                  </label>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Dynamic Workflow Compilation</label>
                    <span>Compiles code blocks to accomplish goal requests when pre-built tool fails.</span>
                  </div>
                  <label className="switch">
                    <input 
                      type="checkbox" 
                      checked={dynamicWorkflow} 
                      onChange={(e) => setDynamicWorkflow(e.target.checked)} 
                    />
                    <span className="slider round"></span>
                  </label>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Autonomous Auto-Recovery</label>
                    <span>Triggers automatic retry or replanning loops on tool execution fail.</span>
                  </div>
                  <label className="switch">
                    <input 
                      type="checkbox" 
                      checked={autoRecovery} 
                      onChange={(e) => setAutoRecovery(e.target.checked)} 
                    />
                    <span className="slider round"></span>
                  </label>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Maximum Step Retry Depth</label>
                    <span>Limit agent retries for a single task step: {retryDepth}</span>
                  </div>
                  <input 
                    type="range" 
                    className="setting-range" 
                    min="1" 
                    max="5" 
                    step="1" 
                    value={retryDepth} 
                    onChange={(e) => setRetryDepth(parseInt(e.target.value, 10))} 
                  />
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Visual UI Fallbacks</label>
                    <span>Fallback to screenshot-template matching if CSS selectors fail.</span>
                  </div>
                  <label className="switch">
                    <input 
                      type="checkbox" 
                      checked={visualFallback} 
                      onChange={(e) => setVisualFallback(e.target.checked)} 
                    />
                    <span className="slider round"></span>
                  </label>
                </div>
              </div>
            </div>

            <div className="panel-telemetry">
              <AutomationStepsLog isExecuting={true} retryDepth={retryDepth} />
            </div>
          </div>
        );

      case 'visual_cognition':
        return (
          <div className="settings-panel-grid">
            <div className="panel-controls">
              <h2 className="panel-title">Visual Cognition</h2>
              <div className="settings-group">
                <div className="setting-item">
                  <div className="setting-info">
                    <label>Visual Reasoning Engine</label>
                    <span>Processes browser screenshots to plan coordinates for clicking elements.</span>
                  </div>
                  <label className="switch">
                    <input 
                      type="checkbox" 
                      checked={visualReasoning} 
                      onChange={(e) => setVisualReasoning(e.target.checked)} 
                    />
                    <span className="slider round"></span>
                  </label>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Deep OCR Layout Recognition</label>
                    <span>Read text blocks directly from captured screen frames.</span>
                  </div>
                  <label className="switch">
                    <input 
                      type="checkbox" 
                      checked={ocrEngine} 
                      onChange={(e) => setOcrEngine(e.target.checked)} 
                    />
                    <span className="slider round"></span>
                  </label>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Screenshot Analysis</label>
                    <span>Save frame screenshots during automation steps for debug reviews.</span>
                  </div>
                  <label className="switch">
                    <input 
                      type="checkbox" 
                      checked={screenshotAnalysis} 
                      onChange={(e) => setScreenshotAnalysis(e.target.checked)} 
                    />
                    <span className="slider round"></span>
                  </label>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Layout Spatial Understanding</label>
                    <span>Analyze DOM structures to predict element locations.</span>
                  </div>
                  <label className="switch">
                    <input 
                      type="checkbox" 
                      checked={layoutUnderstanding} 
                      onChange={(e) => setLayoutUnderstanding(e.target.checked)} 
                    />
                    <span className="slider round"></span>
                  </label>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Interface Memory Model</label>
                    <span>Caches spatial locations of buttons to avoid scanning every time.</span>
                  </div>
                  <label className="switch">
                    <input 
                      type="checkbox" 
                      checked={interfaceMemory} 
                      onChange={(e) => setInterfaceMemory(e.target.checked)} 
                    />
                    <span className="slider round"></span>
                  </label>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>CAPTCHA Deflection System</label>
                    <span>Detects active CAPTCHAs and requests user/secondary solve fallback.</span>
                  </div>
                  <label className="switch">
                    <input 
                      type="checkbox" 
                      checked={captchaDetection} 
                      onChange={(e) => setCaptchaDetection(e.target.checked)} 
                    />
                    <span className="slider round"></span>
                  </label>
                </div>
              </div>
            </div>

            <div className="panel-telemetry">
              <LayoutMonitorScanner ocr={ocrEngine} layout={layoutUnderstanding} />
            </div>
          </div>
        );

      case 'recovery_healing':
        return (
          <div className="settings-panel-grid">
            <div className="panel-controls">
              <h2 className="panel-title">Recovery & Healing</h2>
              <div className="settings-group">
                <div className="setting-item">
                  <div className="setting-info">
                    <label>Adaptive System Re-Planning</label>
                    <span>Dynamically rebuild workflow plans when critical errors are encountered.</span>
                  </div>
                  <label className="switch">
                    <input 
                      type="checkbox" 
                      checked={adaptiveRecovery} 
                      onChange={(e) => setAdaptiveRecovery(e.target.checked)} 
                    />
                    <span className="slider round"></span>
                  </label>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Replanning Aggressiveness</label>
                    <span>Configures willingness to generate alternative paths rather than stopping.</span>
                  </div>
                  <NeuralDropdown 
                    options={['Low (Safe)', 'Moderate', 'High (Aggressive)']}
                    value={replanningAggressiveness}
                    onChange={setReplanningAggressiveness}
                  />
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Self-Healing Iteration Limits</label>
                    <span>Maximum recovery attempt cycles allowed per plan task: {selfHealingDepth}</span>
                  </div>
                  <input 
                    type="range" 
                    className="setting-range" 
                    min="1" 
                    max="10" 
                    value={selfHealingDepth} 
                    onChange={(e) => setSelfHealingDepth(parseInt(e.target.value, 10))} 
                  />
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Standard Fallback Strategy</label>
                    <span>Final system behavior when healing routes exhaust limit checks.</span>
                  </div>
                  <NeuralDropdown 
                    options={['Retry Step', 'Replan Task', 'Human Intervention']}
                    value={fallbackStrategy}
                    onChange={setFallbackStrategy}
                  />
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Real-Time Anomaly Scanner</label>
                    <span>Uses predictive modeling to verify that tools generate expected outputs.</span>
                  </div>
                  <label className="switch">
                    <input 
                      type="checkbox" 
                      checked={anomalyDetection} 
                      onChange={(e) => setAnomalyDetection(e.target.checked)} 
                    />
                    <span className="slider round"></span>
                  </label>
                </div>
              </div>
            </div>

            <div className="panel-telemetry">
              <HealingTimeline depth={selfHealingDepth} replanSpeed={replanningAggressiveness} />
            </div>
          </div>
        );

      case 'tool_synthesis':
        return (
          <div className="settings-panel-grid">
            <div className="panel-controls">
              <h2 className="panel-title">Tool Synthesis</h2>
              <div className="settings-group">
                <div className="setting-item">
                  <div className="setting-info">
                    <label>Dynamic Tool Generation</label>
                    <span>Allow the cognitive parser to compile code snippets to synthesize new tools.</span>
                  </div>
                  <label className="switch">
                    <input 
                      type="checkbox" 
                      checked={toolSynthesis} 
                      onChange={(e) => setToolSynthesis(e.target.checked)} 
                    />
                    <span className="slider round"></span>
                  </label>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Compilation Validation Strictness</label>
                    <span>Sanity check layers run prior to loading synthesized tools in shell memory.</span>
                  </div>
                  <NeuralDropdown 
                    options={['Sandbox (Safe)', 'Medium', 'Strict Verification']}
                    value={validationStrictness}
                    onChange={setValidationStrictness}
                  />
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Auto-Promote Generated Tools</label>
                    <span>Permanently register synthesized tools if successful over 5 trials.</span>
                  </div>
                  <label className="switch">
                    <input 
                      type="checkbox" 
                      checked={autoApproveTools} 
                      onChange={(e) => setAutoApproveTools(e.target.checked)} 
                    />
                    <span className="slider round"></span>
                  </label>
                </div>
              </div>
            </div>

            <div className="panel-telemetry">
              <ToolPipeline validation={validationStrictness} />
            </div>
          </div>
        );

      case 'security_privacy':
        return (
          <div className="settings-panel-grid">
            <div className="panel-controls">
              <h2 className="panel-title">Security & Privacy</h2>
              <div className="settings-group">
                <div className="setting-item">
                  <div className="setting-info">
                    <label>Face Biometric Authentication</label>
                    <span>Verify user identity via front-facing camera scans before executing shell command tasks.</span>
                  </div>
                  <label className="switch">
                    <input 
                      type="checkbox" 
                      checked={faceAuth} 
                      onChange={(e) => setFaceAuth(e.target.checked)} 
                    />
                    <span className="slider round"></span>
                  </label>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Vocal Print Biometric</label>
                    <span>Verify voice command identity against stored user vocal models.</span>
                  </div>
                  <label className="switch">
                    <input 
                      type="checkbox" 
                      checked={voiceAuth} 
                      onChange={(e) => setVoiceAuth(e.target.checked)} 
                    />
                    <span className="slider round"></span>
                  </label>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Secure Memory Vault</label>
                    <span>Stores sensitive credentials and personal data inside a local crypt-vault.</span>
                  </div>
                  <label className="switch">
                    <input 
                      type="checkbox" 
                      checked={secureMemoryVault} 
                      onChange={(e) => setSecureMemoryVault(e.target.checked)} 
                    />
                    <span className="slider round"></span>
                  </label>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Encrypted DB Storage</label>
                    <span>Applies AES-256 block encryption to persistent MongoDB logs.</span>
                  </div>
                  <label className="switch">
                    <input 
                      type="checkbox" 
                      checked={encryptedStorage} 
                      onChange={(e) => setEncryptedStorage(e.target.checked)} 
                    />
                    <span className="slider round"></span>
                  </label>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>API Credentials Key</label>
                    <span>Active secret access token used for external AI model API pipelines.</span>
                  </div>
                  <div className="relative w-[280px]">
                    <input 
                      type="password" 
                      className="setting-input w-full pr-10" 
                      value={apiKeyManager} 
                      onChange={(e) => setApiKeyManager(e.target.value)} 
                    />
                    <Key size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-white/40" />
                  </div>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Local-Only Processing Mode</label>
                    <span>Restricts calls to external networks. Disables cloud LLaMA synthesizers.</span>
                  </div>
                  <label className="switch">
                    <input 
                      type="checkbox" 
                      checked={localOnlyMode} 
                      onChange={(e) => setLocalOnlyMode(e.target.checked)} 
                    />
                    <span className="slider round"></span>
                  </label>
                </div>
              </div>
            </div>

            <div className="panel-telemetry">
              <BiometricScanner activeScan={faceAuth} />
            </div>
          </div>
        );

      case 'performance_opt':
        return (
          <div className="settings-panel-grid">
            <div className="panel-controls">
              <h2 className="panel-title">System Performance</h2>
              <div className="settings-group">
                <div className="setting-item">
                  <div className="setting-info">
                    <label>Core Performance Mode</label>
                    <span>Balance CPU clock priorities, background processes, and animation workloads.</span>
                  </div>
                  <div className="segmented-control">
                    {['Eco', 'Balanced', 'Turbo'].map((mode) => (
                      <button 
                        key={mode}
                        className={`segmented-btn ${energyMode === mode ? 'active' : ''}`}
                        onClick={() => setEnergyMode(mode)}
                      >
                        {mode}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>UI Visuals Intensity</label>
                    <span>Configures frame limits and glow layers on central dashboard UI: {animationIntensity}%</span>
                  </div>
                  <input 
                    type="range" 
                    className="setting-range" 
                    min="0" 
                    max="100" 
                    step="5" 
                    value={animationIntensity} 
                    onChange={(e) => setAnimationIntensity(parseInt(e.target.value, 10))} 
                  />
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Background Index Sync</label>
                    <span>Allow file scanners to run silently when the terminal host is idle.</span>
                  </div>
                  <label className="switch">
                    <input 
                      type="checkbox" 
                      checked={backgroundProcessing} 
                      onChange={(e) => setBackgroundProcessing(e.target.checked)} 
                    />
                    <span className="slider round"></span>
                  </label>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Cache Auto-Purge</label>
                    <span>Cleans browser agent states and tool compilation binaries every 24 hours.</span>
                  </div>
                  <label className="switch">
                    <input 
                      type="checkbox" 
                      checked={cacheAutoPurge} 
                      onChange={(e) => setCacheAutoPurge(e.target.checked)} 
                    />
                    <span className="slider round"></span>
                  </label>
                </div>
              </div>
            </div>

            <div className="panel-telemetry">
              <RealtimeHardwarePlot />
            </div>
          </div>
        );

      case 'integrations':
        return (
          <div className="settings-panel-grid">
            <div className="panel-controls flex-1">
              <h2 className="panel-title">Connected Services</h2>
              <div className="settings-group grid grid-cols-2 gap-4">
                {Object.keys(integrationsState).map((serviceName) => (
                  <div 
                    key={serviceName} 
                    className={`integration-card ${integrationsState[serviceName] ? 'connected' : ''}`}
                  >
                    <div className="card-top">
                      <span className="service-name text-sm font-bold uppercase tracking-wider">{serviceName}</span>
                      <span className={`status-tag ${integrationsState[serviceName] ? 'active' : 'inactive'}`}>
                        {integrationsState[serviceName] ? 'Connected' : 'Offline'}
                      </span>
                    </div>
                    <p className="text-[10px] text-white/50 my-1">
                      {serviceName === 'groq' ? 'Groq LPU Acceleration SDK' :
                       serviceName === 'mongodb' ? 'NoSQL MongoDB Atlas' :
                       `External integration hooks for ${serviceName}`}
                    </p>
                    <button 
                      className={`card-btn mt-2 ${integrationsState[serviceName] ? '' : 'primary'}`}
                      onClick={() => setIntegrationsState(prev => ({
                        ...prev,
                        [serviceName]: !prev[serviceName]
                      }))}
                    >
                      {integrationsState[serviceName] ? 'Disconnect' : 'Connect Link'}
                    </button>
                  </div>
                ))}
              </div>
            </div>

            <div className="panel-telemetry">
              <IntegrationMatrix />
            </div>
          </div>
        );

      case 'developer_console':
        return (
          <div className="settings-panel-grid">
            <div className="panel-controls flex-1">
              <h2 className="panel-title">Developer Console</h2>
              <div className="settings-group">
                <div className="setting-item">
                  <div className="setting-info">
                    <label>Active Modules Status</label>
                    <span>Subsystems check status and connection state logs.</span>
                  </div>
                  <div className="flex gap-2 font-mono text-[10px] text-cyan-400">
                    <span className="bg-cyan-500/10 px-2 py-1 border border-cyan-500/30 rounded">STT: OK</span>
                    <span className="bg-purple-500/10 px-2 py-1 border border-purple-500/30 rounded">NLP: SMART</span>
                    <span className="bg-emerald-500/10 px-2 py-1 border border-emerald-500/30 rounded">DB: ONLINE</span>
                  </div>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Active Tool Registry</label>
                    <span>Reload dynamic discovery registry. Discoveries cache has 32 tools.</span>
                  </div>
                  <button className="action-btn flex items-center gap-2">
                    <RefreshCw size={14} className="animate-spin" /> Reload Tools Registry
                  </button>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Download Diagnostics Trace</label>
                    <span>Extract compiled trace logs for ReAct steps in ZIP package.</span>
                  </div>
                  <button className="action-btn">
                    Download ZIP
                  </button>
                </div>
              </div>
            </div>

            <div className="panel-telemetry flex-1">
              <DeveloperTerminal />
            </div>
          </div>
        );

      case 'experimental_features':
        return (
          <div className="settings-panel-grid">
            <div className="panel-controls">
              <h2 className="panel-title text-amber-500">Experimental Settings</h2>
              
              <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4 mb-6 flex gap-3 items-start max-w-[600px]">
                <AlertTriangle size={24} className="text-amber-500 shrink-0 mt-0.5" />
                <div className="text-xs text-amber-500/80 font-mono">
                  <p className="font-bold uppercase tracking-wider text-amber-500">☢ CAUTION: UNSTABLE EXPERIMENTAL ARCHITECTURE</p>
                  <p className="mt-1">
                    Enabling features in this layer bypasses sandbox limits, allows direct system modification, and utilizes untested generative models.
                  </p>
                </div>
              </div>

              <div className="settings-group">
                <div className="setting-item">
                  <div className="setting-info">
                    <label>Multi-Agent Swarm Mode</label>
                    <span>Deploy a decentralized swarm coordinates framework (Can trigger high API load).</span>
                  </div>
                  <label className="switch">
                    <input 
                      type="checkbox" 
                      checked={multiAgentSwarm} 
                      onChange={(e) => setMultiAgentSwarm(e.target.checked)} 
                    />
                    <span className="slider round"></span>
                  </label>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Meta-Cognitive Self-Evolution</label>
                    <span>Enables system self-evaluation and code adjustment during task observation loops.</span>
                  </div>
                  <label className="switch">
                    <input 
                      type="checkbox" 
                      checked={metaCognition} 
                      onChange={(e) => setMetaCognition(e.target.checked)} 
                    />
                    <span className="slider round"></span>
                  </label>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Predictive Workflow Caching</label>
                    <span>Uses models to pre-compute task execution steps before user speech ends.</span>
                  </div>
                  <label className="switch">
                    <input 
                      type="checkbox" 
                      checked={predictivePlanning} 
                      onChange={(e) => setPredictivePlanning(e.target.checked)} 
                    />
                    <span className="slider round"></span>
                  </label>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Self-Evolving Tool Compressor</label>
                    <span>Compresses synthesized code utilities into lightweight custom binaries.</span>
                  </div>
                  <label className="switch">
                    <input 
                      type="checkbox" 
                      checked={selfEvolvingArch} 
                      onChange={(e) => setSelfEvolvingArch(e.target.checked)} 
                    />
                    <span className="slider round"></span>
                  </label>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Experimental Vision Models</label>
                    <span>Deploy multi-modal vision trackers for spatial interface memory.</span>
                  </div>
                  <label className="switch">
                    <input 
                      type="checkbox" 
                      checked={experimentalVision} 
                      onChange={(e) => setExperimentalVision(e.target.checked)} 
                    />
                    <span className="slider round"></span>
                  </label>
                </div>
              </div>
            </div>

            <div className="panel-telemetry">
              <QuantumProjectionChip />
            </div>
          </div>
        );

      default:
        return <div className="settings-panel"><h2 className="panel-title">Coming Soon</h2></div>;
    }
  };

  return (
    <div className="settings-container">
      {/* SIDEBAR */}
      <aside className={`settings-sidebar ${isSidebarCollapsed ? 'collapsed' : ''}`}>
        <div className="sidebar-header flex items-center justify-between">
          {!isSidebarCollapsed && (
            <div>
              <h1 className="font-serif italic text-2xl text-cyan-400">Settings</h1>
              <p className="text-[9px] uppercase tracking-widest text-cyan-400 opacity-60">System Core V2.0</p>
            </div>
          )}
          <button 
            className="collapse-btn text-white/50 hover:text-white"
            onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
          >
            {isSidebarCollapsed ? <Menu size={18} /> : <ChevronLeft size={18} />}
          </button>
        </div>

        <nav className="sidebar-nav custom-scrollbar">
          {tabs.map(tab => (
            <button 
              key={tab.id}
              className={`nav-link ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
              title={tab.label}
            >
              <span className="nav-icon">{tab.icon}</span>
              {!isSidebarCollapsed && <span className="nav-label">{tab.label}</span>}
              {!isSidebarCollapsed && activeTab === tab.id && <ChevronRight size={14} className="active-arrow" />}
            </button>
          ))}
        </nav>
      </aside>

      {/* MAIN CONTENT */}
      <main className="settings-main">
        <header className="main-header">
          <div className="header-breadcrumbs">
            <span>Settings</span>
            <ChevronRight size={14} />
            <span className="active-breadcrumb">
              {tabs.find(t => t.id === activeTab)?.label}
            </span>
          </div>
          <button className="save-btn" onClick={handleSave}>
            <Save size={18} />
            Save Changes
          </button>
        </header>

        <section className="main-scroll-area custom-scrollbar">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, x: 15, filter: 'blur(4px)' }}
            animate={{ opacity: 1, x: 0, filter: 'blur(0px)' }}
            transition={{ 
              type: "spring",
              stiffness: 110,
              damping: 18,
              mass: 1
            }}
            className="h-full"
          >
            {renderContent()}
          </motion.div>
        </section>
      </main>

      {/* TOAST NOTIFICATION */}
      <AnimatePresence>
        {showToast && (
          <motion.div 
            className="settings-toast"
            initial={{ opacity: 0, y: 50, x: "-50%" }}
            animate={{ opacity: 1, y: 0, x: "-50%" }}
            exit={{ opacity: 0, y: 50, x: "-50%" }}
          >
            <CheckCircle2 size={20} className="text-cyan-400" />
            <span>Configuration synchronized successfully.</span>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default SettingsPage;
