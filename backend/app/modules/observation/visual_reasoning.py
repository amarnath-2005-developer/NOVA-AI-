"""
NOVA AI 2.0 — Multi-Modal Visual Reasoning Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Enables visual cognition, screen layout understanding, dynamic UI navigation,
OCR/VLM failure detection, and dynamic UI element coordinate mapping using LLaMA Vision.
"""

import os
import base64
import certifi
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorClient
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("nova.visual_reasoning")


class VisualReasoningEngine:
    """
    Cognitive visual engine utilizing LLaMA 3.2 Multi-Modal Vision models
    to provide screen understanding, coordinate mapping, and visual failure detection.
    """

    def __init__(self, groq_client: Optional[Groq] = None):
        ca = certifi.where()
        self.db_client = AsyncIOMotorClient(
            os.getenv("MONGODB_URL", "mongodb://localhost:27017"),
            tlsCAFile=ca,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000
        )
        self.db = self.db_client[os.getenv("DATABASE_NAME", "nova_ai")]
        self.collection = self.db["agent_visual_states"]
        
        self.groq_client = groq_client or Groq(api_key=os.getenv("GROQ_API_KEY"))
        # We utilize LLaMA 3.2 11B Vision for high-performance and fast visual inference
        self.model = "llama-3.2-11b-vision-preview"

    async def capture_browser_screenshot(self, browser_page, filename: str = "temp_browser.jpg") -> Optional[str]:
        """Captures a screenshot of the active browser viewport."""
        try:
            temp_dir = os.path.join(os.getcwd(), "backend", "app", "temp")
            os.makedirs(temp_dir, exist_ok=True)
            save_path = os.path.join(temp_dir, filename)
            
            await browser_page.screenshot(path=save_path, type="jpeg", quality=80)
            logger.info(f"Visual Reasoning: Captured browser screenshot: {save_path}")
            return save_path
        except Exception as e:
            logger.error(f"Failed to capture browser screenshot: {e}")
            return None

    async def capture_desktop_screenshot(self, filename: str = "temp_desktop.jpg") -> Optional[str]:
        """Captures a screenshot of the system operating desktop using PyAutoGUI."""
        try:
            temp_dir = os.path.join(os.getcwd(), "backend", "app", "temp")
            os.makedirs(temp_dir, exist_ok=True)
            save_path = os.path.join(temp_dir, filename)
            
            import pyautogui
            screenshot = pyautogui.screenshot()
            screenshot.convert("RGB").save(save_path, "JPEG", quality=80)
            logger.info(f"Visual Reasoning: Captured desktop screenshot: {save_path}")
            return save_path
        except Exception as e:
            logger.error(f"Failed to capture desktop screenshot: {e}")
            return None

    def _encode_image_to_base64(self, image_path: str) -> str:
        """Converts an image file on disk to a base64 encoded UTF-8 string."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    async def query_vision_model(self, image_path: str, prompt: str, schema_type: str = "json_object") -> str:
        """Sends an image and text query to Groq LLaMA Vision model and returns the text response."""
        try:
            base64_image = self._encode_image_to_base64(image_path)
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
            
            completion = self.groq_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,  # Strict temperature for high precision
                max_tokens=600,
                response_format={"type": schema_type} if schema_type == "json_object" else None
            )
            
            return completion.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Groq LLaMA Vision API query failed: {e}")
            raise e

    async def locate_element_visually(self, element_description: str, image_path: str) -> Optional[Tuple[float, float]]:
        """
        Locates target UI elements visually, returning normalized (X, Y) percentages
        (0.0 to 1.0) relative to the top-left of the viewport.
        """
        prompt = f"""You are the Visual UI Navigator for NOVA AI.
Your task is to locate the target element: "{element_description}" on the screen image.
Analyze the layout carefully and locate the exact click target center of this element.

Output a valid JSON object matching this structure EXACTLY. Do not add markdown or comments:
{{
  "x": normalized_x_coordinate_percentage_from_0_to_1,
  "y": normalized_y_coordinate_percentage_from_0_to_1,
  "confidence": score_from_0_to_1
}}"""
        try:
            import json
            raw_response = await self.query_vision_model(image_path, prompt, "json_object")
            result = json.loads(raw_response)
            
            x = float(result.get("x", -1.0))
            y = float(result.get("y", -1.0))
            conf = float(result.get("confidence", 0.0))
            
            if 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0:
                logger.info(f"Visual Reasoning: Located '{element_description}' at ({x:.2f}, {y:.2f}) with confidence {conf:.2f}")
                return x, y
        except Exception as e:
            logger.error(f"Failed to locate element visually: {e}")
        return None

    async def detect_anomalies_visually(self, image_path: str) -> dict:
        """
        Inspects screenshots visually to identify loading states, popups,
        error screens, and CAPTCHA blockades.
        """
        prompt = """You are the Visual Quality Assurance Engine for NOVA AI.
Analyze the provided interface screenshot for any execution barriers or anomalies.
Look out for:
1. CAPTCHAs, security verifications, or bot challenges
2. Modal popups, promo screens, cookies requests, or access dialogs blocking interaction
3. Explicit error notifications, login warnings, or system syntax alerts
4. Blank loading states, loaders, spinners, or unfinished DOM renders

Output a valid JSON object matching this structure EXACTLY. Do not add markdown or comments:
{
  "anomaly_detected": true_or_false,
  "anomaly_type": "CAPTCHA_BARRIER" or "ERROR_DIALOG" or "POPUP_OBSTRUCTION" or "LOADING_BLANK" or "NONE",
  "description": "Short explanation of what was visually detected",
  "suggested_action": "Self-healing resolution (e.g. solve captcha, click close button, reload, wait)"
}"""
        try:
            import json
            raw_response = await self.query_vision_model(image_path, prompt, "json_object")
            result = json.loads(raw_response)
            logger.info(f"Visual Reasoning: Anomaly analysis: {result}")
            return result
        except Exception as e:
            logger.error(f"Visual anomaly detection failed: {e}")
            return {
                "anomaly_detected": False,
                "anomaly_type": "NONE",
                "description": f"Failed to run vision model: {e}",
                "suggested_action": "none"
            }

    async def analyze_layout_semantics(self, image_path: str) -> dict:
        """Segments screen layout visually into logical zones, forms, upload sections, and sidebars."""
        prompt = """You are the Visual Layout Architect for NOVA AI.
Analyze the semantic structural regions on the screen image.
Identify where the major zones are located, such as:
1. Navigation menu/Sidebar
2. Form fields or main content inputs
3. File drop/upload zones
4. Primary call-to-action buttons
5. Dialog popups

Output a valid JSON object matching this structure EXACTLY. Do not add markdown or comments:
{
  "layout_type": "dashboard" or "upload_form" or "search_page" or "login" or "other",
  "regions": [
    {
      "name": "region name (e.g. sidebar, main_form)",
      "x_start": 0.0_to_1.0,
      "y_start": 0.0_to_1.0,
      "width": 0.0_to_1.0,
      "height": 0.0_to_1.0
    }
  ]
}"""
        try:
            import json
            raw_response = await self.query_vision_model(image_path, prompt, "json_object")
            result = json.loads(raw_response)
            
            # Store known layout in MongoDB to build visual state memory
            layout_type = result.get("layout_type", "other")
            await self.collection.update_one(
                {"image_hash": hash(image_path) % 10000000},
                {
                    "$set": {
                        "layout_type": layout_type,
                        "regions": result.get("regions", []),
                        "analyzed_at": datetime.now()
                    }
                },
                upsert=True
            )
            logger.info(f"Visual Reasoning: Layout Semantics mapped layout_type='{layout_type}' with {len(result.get('regions', []))} regions")
            return result
        except Exception as e:
            logger.error(f"Visual layout analysis failed: {e}")
            return {"layout_type": "unknown", "regions": []}
