import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { tts } from '../lib/tts';
import { FileText, Volume2, VolumeX, X, Sparkles } from 'lucide-react';
import './PdfSummaryPopup.css';

const PdfSummaryPopup = ({ title, summary, speechSummary, closeAfter = true, onClose }) => {
  const [isReading, setIsReading] = useState(false);
  const [isMuted, setIsMuted] = useState(false);

  useEffect(() => {
    let active = true;

    const startSpeaking = async () => {
      // 1. Wait for any current speech (like the intro response message) to clear
      while (tts.isSpeaking && active) {
        await new Promise(r => setTimeout(r, 100));
      }

      if (!active) return;

      // 2. Start speaking the summary
      setIsReading(true);
      const textToSpeak = speechSummary || summary.replace(/[#*_\-`]/g, '').substring(0, 250);
      
      await tts.speak(textToSpeak);

      if (!active) return;
      setIsReading(false);

      // 3. Auto-close if requested
      if (closeAfter) {
        await new Promise(r => setTimeout(r, 1000));
        if (active) onClose();
      }
    };

    startSpeaking();

    return () => {
      active = false;
      // Terminate TTS synthesis for this popup on unmount
      tts.synth.cancel();
    };
  }, [summary, speechSummary, closeAfter, onClose]);

  const toggleMute = () => {
    if (isMuted) {
      tts.setMute(false);
      setIsMuted(false);
    } else {
      tts.setMute(true);
      setIsMuted(false);
      setIsReading(false);
    }
  };

  const renderMarkdown = (text) => {
    if (!text) return null;
    const lines = text.split('\n');
    return lines.map((line, i) => {
      const cleanLine = line.trim();
      if (!cleanLine) return <div key={i} className="h-2" />;

      if (cleanLine.startsWith('###')) {
        return (
          <h4 key={i} className="text-cyan-400 font-bold mt-4 mb-2 text-sm tracking-wider uppercase flex items-center gap-2">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
            {cleanLine.replace('###', '').trim()}
          </h4>
        );
      }
      if (cleanLine.startsWith('##')) {
        return (
          <h3 key={i} className="text-cyan-300 font-bold mt-5 mb-2 text-base border-b border-cyan-900/50 pb-1 tracking-wider uppercase">
            {cleanLine.replace('##', '').trim()}
          </h3>
        );
      }
      if (cleanLine.startsWith('#')) {
        return (
          <h2 key={i} className="text-cyan-200 font-extrabold mt-6 mb-3 text-lg tracking-wider uppercase border-b-2 border-cyan-500/30 pb-2">
            {cleanLine.replace('#', '').trim()}
          </h2>
        );
      }
      if (cleanLine.startsWith('-') || cleanLine.startsWith('*')) {
        const boldFormatted = cleanLine.substring(1).trim().split('**').map((part, index) => 
          index % 2 === 1 ? <strong key={index} className="text-cyan-400 font-semibold">{part}</strong> : part
        );
        return (
          <li key={i} className="ml-4 mb-2 list-disc text-gray-300 leading-relaxed text-xs">
            {boldFormatted}
          </li>
        );
      }
      
      const boldFormatted = cleanLine.split('**').map((part, index) => 
        index % 2 === 1 ? <strong key={index} className="text-cyan-400 font-semibold">{part}</strong> : part
      );
      return <p key={i} className="mb-3 text-gray-300 leading-relaxed text-xs">{boldFormatted}</p>;
    });
  };

  return (
    <div className="pdf-summary-overlay">
      <motion.div 
        className="pdf-summary-card"
        initial={{ opacity: 0, scale: 0.9, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.9, y: 20 }}
        transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      >
        {/* Futuristic Scanline Effect */}
        <div className="scanline" />

        {/* Card Header */}
        <div className="pdf-card-header">
          <div className="pdf-header-title">
            <FileText className="w-5 h-5 text-cyan-400 animate-pulse" />
            <div className="title-text-group">
              <span className="subtitle">COMET_CORE_SUMMARY</span>
              <h2 className="title">{title || "Document summary"}</h2>
            </div>
          </div>
          <div className="pdf-header-actions">
            <button className={`mute-btn ${isMuted ? 'muted' : ''}`} onClick={toggleMute} title={isMuted ? "Unmute" : "Mute"}>
              {isMuted ? <VolumeX className="w-4 h-4 text-red-400" /> : <Volume2 className="w-4 h-4 text-cyan-400" />}
            </button>
            <button className="close-btn" onClick={onClose} title="Close Panel">
              <X className="w-4 h-4 text-gray-400" />
            </button>
          </div>
        </div>

        {/* Content body */}
        <div className="pdf-card-content scrollbar-custom">
          {renderMarkdown(summary)}
        </div>

        {/* Card Footer */}
        <div className="pdf-card-footer">
          {isReading ? (
            <div className="voice-visualization">
              <span className="pulse-dot active" />
              <span className="status-text animate-pulse">NOVA READING OVERVIEW...</span>
              <div className="audio-wave">
                <span className="wave-bar" style={{ animationDelay: '0.1s' }} />
                <span className="wave-bar" style={{ animationDelay: '0.3s' }} />
                <span className="wave-bar" style={{ animationDelay: '0.5s' }} />
                <span className="wave-bar" style={{ animationDelay: '0.2s' }} />
                <span className="wave-bar" style={{ animationDelay: '0.4s' }} />
              </div>
            </div>
          ) : (
            <div className="voice-visualization">
              <span className="pulse-dot" />
              <span className="status-text text-gray-500">SYSTEM READY</span>
            </div>
          )}
          
          <button className="done-btn" onClick={onClose}>
            DISMISS
          </button>
        </div>

        {/* Auto close progress indicator */}
        {closeAfter && isReading && (
          <div className="progress-bar-container">
            <motion.div 
              className="progress-bar-fill"
              initial={{ width: "100%" }}
              animate={{ width: "0%" }}
              transition={{ duration: speechSummary ? speechSummary.split(' ').length * 0.45 : 30, ease: 'linear' }}
            />
          </div>
        )}
      </motion.div>
    </div>
  );
};

export default PdfSummaryPopup;
