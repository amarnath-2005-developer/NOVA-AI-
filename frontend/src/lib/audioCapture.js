const AUDIO_CONSTRAINTS = {
  audio: { channelCount: 1, sampleRate: 16000, echoCancellation: true, noiseSuppression: true, autoGainControl: true },
  video: false,
};

export async function createAudioCapture(onSilenceDetected) {
  const stream = await navigator.mediaDevices.getUserMedia(AUDIO_CONSTRAINTS);
  const audioCtx = new AudioContext({ sampleRate: 16000 });
  const source = audioCtx.createMediaStreamSource(stream);
  
  const analyser = audioCtx.createAnalyser();
  analyser.fftSize = 512;
  analyser.smoothingTimeConstant = 0.8;
  
  const highpass = audioCtx.createBiquadFilter();
  highpass.type = 'highpass';
  highpass.frequency.value = 80;

  const compressor = audioCtx.createDynamicsCompressor();
  compressor.threshold.value = -24;
  compressor.knee.value = 30;
  compressor.ratio.value = 4;

  const dest = audioCtx.createMediaStreamDestination();
  source.connect(highpass).connect(compressor).connect(dest);
  source.connect(analyser); // Also route to analyser for VAD

  let recorder = null;
  let chunks = [];
  let isRecording = false;
  let vadInterval = null;
  let silenceStart = 0;

  const SILENCE_THRESHOLD = 15; // Higher threshold for noisy environments
  const SILENCE_DURATION = 2000; // 2.0s silence trigger to allow natural pauses

  const checkVAD = () => {
    if (!isRecording) return;
    
    const dataArray = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteFrequencyData(dataArray);
    
    // focus on speech frequencies (roughly 80Hz to 1000Hz for basic VAD)
    let sum = 0;
    const startBin = 2; // skip very low rumble
    const endBin = 40;  // focus on vocal range
    for (let i = startBin; i < endBin; i++) sum += dataArray[i];
    const average = sum / (endBin - startBin);

    if (average < SILENCE_THRESHOLD) {
      if (silenceStart === 0) silenceStart = Date.now();
      else if (Date.now() - silenceStart > SILENCE_DURATION) {
        if (onSilenceDetected) onSilenceDetected(); // Trigger stop
      }
    } else {
      silenceStart = 0; // Reset
    }
  };

  let timeoutId = null;

  return {
    start() {
      chunks = [];
      isRecording = true;
      silenceStart = 0;
      recorder = new MediaRecorder(dest.stream);
      recorder.ondataavailable = (e) => {
          if (e.data.size > 0) chunks.push(e.data);
      };
      
      // Start with timeslice to ensure data is pushed regularly
      recorder.start(200);
      
      if (vadInterval) clearInterval(vadInterval);
      vadInterval = setInterval(checkVAD, 100);

      // Safety timeout: stop recording after 15 seconds max
      if (timeoutId) clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
          if (isRecording && onSilenceDetected) onSilenceDetected();
      }, 15000);
    },
    async stop() {
      isRecording = false;
      if (vadInterval) clearInterval(vadInterval);
      if (timeoutId) clearTimeout(timeoutId);
      
      return new Promise((resolve) => {
        recorder.onstop = () => {
            const blob = new Blob(chunks, { type: 'audio/webm' });
            resolve(blob);
        };
        if (recorder.state !== 'inactive') recorder.stop();
        else resolve(new Blob(chunks, { type: 'audio/webm' }));
      });
    },
    destroy() {
      stream.getTracks().forEach(t => t.stop());
      audioCtx.close();
      if (timeoutId) clearTimeout(timeoutId);
    }
  };
}
