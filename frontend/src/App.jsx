import React, { useState, useEffect } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import NeuralVoiceGraph from './components/NeuralVoiceGraph';
import Navbar from './components/Navbar';
import LoginPage from './pages/Login';
import SettingsPage from './pages/Settings';
import SpeechConsole from './components/SpeechConsole';
import StatusConsole from './components/StatusConsole';
import SystemInfoWidget from './components/SystemInfoWidget';
import SystemStatusPanel from './components/SystemStatusPanel';
import ActivityMonitorPanel from './components/ActivityMonitorPanel';
import { EtheralShadow } from './components/ui/etheral-shadow';
import PdfSummaryPopup from './components/PdfSummaryPopup';

function App() {
  const [currentView, setCurrentView] = useState('home');
  const [activeSummary, setActiveSummary] = useState(null);

  useEffect(() => {
    const handlePdfSummary = (e) => {
      setActiveSummary(e.detail);
    };
    window.addEventListener('nova-pdf-summary', handlePdfSummary);
    return () => window.removeEventListener('nova-pdf-summary', handlePdfSummary);
  }, []);

  const handleNavigate = (view) => {
    setCurrentView(view);
  };

  const pageVariants = {
    initial: { opacity: 0, x: 30, filter: 'blur(10px)' },
    animate: { 
      opacity: 1, 
      x: 0, 
      filter: 'blur(0px)',
      transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] }
    },
    exit: { 
      opacity: 0, 
      x: -30, 
      filter: 'blur(10px)',
      transition: { duration: 0.4, ease: [0.22, 1, 0.36, 1] }
    }
  };

  return (
    <div className="min-h-screen bg-[#010101] text-white relative overflow-hidden">
      
      {/* GLOBAL NAVBAR */}
      <div className="fixed top-0 left-0 w-full z-[1000] pointer-events-none">
        <div className="pointer-events-auto">
          <Navbar onNavigate={handleNavigate} currentView={currentView} />
        </div>
      </div>

      {/* PAGE TRANSITIONS */}
      <AnimatePresence mode="wait">
        {currentView === 'home' && (
          <motion.div
            key="home"
            variants={pageVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            className="w-full h-screen relative z-10"
          >
            {/* ETHERAL SHADOW BACKGROUND */}
            <div className="absolute inset-0 z-0">
              <EtheralShadow 
                color="rgba(43, 205, 255, 0.45)"
                animation={{ scale: 80, speed: 10 }}
                noise={{ scale: 1, opacity: 0.15 }}
                className="z-0"
              />
            </div>
            <NeuralVoiceGraph />
            <SpeechConsole />
            <StatusConsole />
            <SystemInfoWidget />
            <SystemStatusPanel />
            <ActivityMonitorPanel />

            {/* Glassmorphic PDF Summary Modal */}
            <AnimatePresence>
              {activeSummary && (
                <PdfSummaryPopup 
                  title={activeSummary.title}
                  summary={activeSummary.summary}
                  speechSummary={activeSummary.speech_summary}
                  closeAfter={activeSummary.close_after}
                  onClose={() => setActiveSummary(null)}
                />
              )}
            </AnimatePresence>
          </motion.div>
        )}


        {currentView === 'login' && (
          <motion.div
            key="login"
            variants={pageVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            className="w-full h-screen relative z-10"
          >
            <LoginPage onNavigate={handleNavigate} />
          </motion.div>
        )}

        {currentView === 'settings' && (
          <motion.div
            key="settings"
            variants={pageVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            className="w-full h-screen relative z-10"
          >
            <SettingsPage onNavigate={handleNavigate} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default App;
