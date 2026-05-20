import React, { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';

/**
 * OrganicLine: The core "blob" structure from Snippet 1.
 * We've added "Neural" connectivity and nodes at the ends.
 */
class OrganicLine {
  constructor(w, h) {
    this.w = w;
    this.h = h;
    this.x = w / 2;
    this.y = h / 2;
    this.reset();
  }

  reset() {
    this.endAngle = Math.random() * 360;
    this.endSpeed = (Math.random() * 0.1 + 0.1) / 40;
    this.endDir = Math.random() < 0.5 ? -1 : 1;
    this.endChangeFreq = Math.floor(Math.random() * 200) + 100;

    this.c1Angle = Math.random() * 360;
    this.c1Speed = (Math.random() * 0.2 + 0.1) / 20;
    this.c1Dir = Math.random() < 0.5 ? -1 : 1;
    this.c1ChangeFreq = Math.floor(Math.random() * 200) + 100;

    this.c2Angle = Math.random() * 360;
    this.c2Speed = (Math.random() * 0.2 + 0.1) / 20;
    this.c2Dir = Math.random() < 0.5 ? -1 : 1;
    this.c2ChangeFreq = Math.floor(Math.random() * 200) + 100;

    this.endPos = { x: 0, y: 0 };
  }

  move(vol) {
    // Immediate voice reaction speed boost
    const boost = 1 + vol * 25;

    this.endChangeFreq--;
    if (this.endChangeFreq <= 0) {
      this.endDir *= -1;
      this.endChangeFreq = Math.floor(Math.random() * 200) + 100;
    }
    this.endAngle += this.endSpeed * this.endDir * boost;

    this.c1ChangeFreq--;
    if (this.c1ChangeFreq <= 0) {
      this.c1Dir *= -1;
      this.c1ChangeFreq = Math.floor(Math.random() * 200) + 100;
    }
    this.c1Angle += this.c1Speed * this.c1Dir * boost;

    this.c2ChangeFreq--;
    if (this.c2ChangeFreq <= 0) {
      this.c2Dir *= -1;
      this.c2ChangeFreq = Math.floor(Math.random() * 200) + 100;
    }
    this.c2Angle += this.c2Speed * this.c2Dir * boost;
  }

  getPoint(x, y, dist, ang) {
    const rad = ang * (Math.PI / 180);
    return {
      x: x + Math.cos(rad) * dist,
      y: y + Math.sin(rad) * dist,
    };
  }

  updatePoints(vol) {
    // Moderate size: base 100-140px radius
    const distMod = 1 + vol * 1.5;
    this.c1 = this.getPoint(this.x, this.y, 80 * distMod, this.c1Angle);
    this.endPos = this.getPoint(this.x, this.y, 140 * distMod, this.endAngle);
    this.c2 = this.getPoint(this.endPos.x, this.endPos.y, 80 * distMod, this.c2Angle);
  }

  draw(ctx, vol) {
    ctx.beginPath();
    ctx.moveTo(this.x, this.y);
    ctx.bezierCurveTo(this.c1.x, this.c1.y, this.c2.x, this.c2.y, this.endPos.x, this.endPos.y);
    
    // Brighter cyan stroke
    ctx.strokeStyle = `rgba(43, 205, 255, ${0.3 + vol * 0.5})`;
    ctx.lineWidth = 1.2;
    ctx.stroke();

    // Brighter "Neural Node" (Snippet 2 logic)
    ctx.beginPath();
    ctx.arc(this.endPos.x, this.endPos.y, 3 + vol * 5, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(43, 205, 255, ${0.7 + vol * 0.3})`;
    ctx.fill();
  }
}

const NeuralVoiceGraph = () => {
  const canvasRef = useRef(null);
  const [isListening, setIsListening] = useState(false);
  const linesRef = useRef([]);
  const analyserRef = useRef(null);
  const dataRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    let animationId;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      // Reduced to 35 lines for better performance (O(N^2) optimization)
      linesRef.current = [...Array(35)].map(() => new OrganicLine(canvas.width, canvas.height));
    };
    window.addEventListener('resize', resize);
    resize();

    let streamRef = null;
    let audioCtxRef = null;

    const initMic = async () => {
      try {
        streamRef = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioCtxRef = new (window.AudioContext || window.webkitAudioContext)();
        const source = audioCtxRef.createMediaStreamSource(streamRef);
        const analyser = audioCtxRef.createAnalyser();
        analyser.fftSize = 256;
        source.connect(analyser);
        analyserRef.current = analyser;
        dataRef.current = new Uint8Array(analyser.frequencyBinCount);
        setIsListening(true);
      } catch (e) { console.error("Mic error:", e); }
    };
    initMic();

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      let vol = 0;
      if (analyserRef.current && dataRef.current) {
        analyserRef.current.getByteFrequencyData(dataRef.current);
        let sum = 0;
        for (let i = 1; i < 15; i++) sum += dataRef.current[i];
        const avg = sum / 14;
        if (avg > 15) vol = (avg - 15) / 200;
      }

      // 1. Update and Draw Lines
      ctx.shadowColor = "rgba(43, 205, 255, 1)";
      ctx.shadowBlur = 8 + vol * 15;
      
      linesRef.current.forEach(line => {
        line.move(vol);
        line.updatePoints(vol);
        line.draw(ctx, vol);
      });

      // 2. Draw "Neural Links" with optimized distance check
      ctx.shadowBlur = 0;
      const maxDist = 120 + vol * 100;
      const lines = linesRef.current;
      const len = lines.length;

      for (let i = 0; i < len; i++) {
        const p1 = lines[i].endPos;
        // Optimization: only check half the connections to reduce CPU load
        for (let j = i + 1; j < len; j++) {
          const p2 = lines[j].endPos;
          const dx = p1.x - p2.x;
          const dy = p1.y - p2.y;
          // Fast distance check before hypot
          if (Math.abs(dx) < maxDist && Math.abs(dy) < maxDist) {
            const distSq = dx * dx + dy * dy;
            if (distSq < maxDist * maxDist) {
              const dist = Math.sqrt(distSq);
              ctx.beginPath();
              ctx.moveTo(p1.x, p1.y);
              ctx.lineTo(p2.x, p2.y);
              ctx.strokeStyle = `rgba(43, 205, 255, ${(1 - dist / maxDist) * (0.06 + vol * 0.2)})`;
              ctx.lineWidth = 0.6;
              ctx.stroke();
            }
          }
        }
      }

      animationId = requestAnimationFrame(render);
    };
    render();

    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(animationId);
      
      // Hardware leak fix: ensure microphone and audio context are released
      if (streamRef) {
          streamRef.getTracks().forEach(track => track.stop());
      }
      if (audioCtxRef && audioCtxRef.state !== 'closed') {
          audioCtxRef.close();
      }
    };
  }, []);

  const handleStart = () => {
    // Resume AudioContext if it was suspended (browser policy)
    if (analyserRef.current && analyserRef.current.context.state === 'suspended') {
      analyserRef.current.context.resume();
    }
  };

  return (
    <div 
      className="relative w-full h-full overflow-hidden flex items-center justify-center cursor-pointer"
      onClick={handleStart}
    >
      <canvas ref={canvasRef} className="absolute inset-0 z-10 pointer-events-none" />
      
      {/* Central Indicator */}
      <div className="relative z-20 flex flex-col items-center gap-6">
        <motion.div 
          animate={{
            scale: isListening ? [1, 1.05, 1] : 1,
            borderColor: isListening ? "rgba(43, 205, 255, 0.4)" : "rgba(255, 255, 255, 0.1)"
          }}
          transition={{ duration: 2, repeat: Infinity }}
          className="w-32 h-32 rounded-full border flex items-center justify-center backdrop-blur-sm"
        >
          <div className={`w-16 h-16 rounded-full border-2 transition-all duration-300 ${isListening ? 'border-cyan-400 shadow-[0_0_20px_rgba(43,205,255,0.5)]' : 'border-white/10'}`} />
        </motion.div>
        <p className="text-[10px] font-black tracking-[0.5em] uppercase text-cyan-400/50">Neural Synthesis Active</p>
      </div>
    </div>
  );
};

export default NeuralVoiceGraph;
