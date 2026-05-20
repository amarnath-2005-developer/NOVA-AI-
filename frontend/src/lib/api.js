const API_BASE_URL = "http://localhost:8000/api/v1";

export const sendCommand = async (text) => {
  const user_id = localStorage.getItem('nova_active_user') || "amarnath";
  const response = await fetch(`${API_BASE_URL}/command`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, user_id }),
  });
  return response.json();
};

export const transcribeAudio = async (audioBlob) => {
  const formData = new FormData();
  formData.append("file", audioBlob, "recording.webm");
  const response = await fetch(`${API_BASE_URL}/transcribe`, {
    method: "POST",
    body: formData,
  });
  return response.json();
};
