import base64
import json
import re
import requests
from core.config import Config

class MultiModalLLMClient:
    """
    Resilient LLM & Vision engine with:
      - Primary: Google Gemini 2.5 Flash (Text & Vision)
      - Automatic Failover: Groq Llama-3.3-70B-Versatile (Text)
      - Structured JSON parsing & live failover simulation support
    """

    @staticmethod
    def _extract_json(text: str) -> dict:
        text = text.strip()
        fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if fence_match:
            text = fence_match.group(1)
        else:
            brace_match = re.search(r"(\{.*\})", text, re.DOTALL)
            if brace_match:
                text = brace_match.group(1)
        return json.loads(text)

    @staticmethod
    def _is_valid_key(key: str) -> bool:
        if not key:
            return False
        placeholders = ["your_gemini_api_key_here", "your_groq_api_key_here", "your_api_key"]
        return key.lower() not in placeholders and len(key) > 12

    @classmethod
    def generate_json(cls, system_prompt: str, user_prompt: str) -> tuple[dict, str]:
        gemini_ready = cls._is_valid_key(Config.GEMINI_API_KEY) and not Config.FORCE_GROQ_FAILOVER
        groq_ready = cls._is_valid_key(Config.GROQ_API_KEY)

        # 1. Try Primary: Gemini 2.5 Flash (unless Force Groq Failover is toggled in UI)
        if gemini_ready:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{Config.GEMINI_MODEL}:generateContent?key={Config.GEMINI_API_KEY}"
                payload = {
                    "system_instruction": {"parts": [{"text": system_prompt}]},
                    "contents": [{"parts": [{"text": user_prompt}]}],
                    "generationConfig": {
                        "temperature": 0.1,
                        "responseMimeType": "application/json"
                    }
                }
                r = requests.post(url, json=payload, timeout=20)
                r.raise_for_status()
                raw_text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                return cls._extract_json(raw_text), "Gemini 2.5 Flash (Primary)"
            except Exception as e:
                print(f"[Gemini Primary Failover Triggered] {e}")

        # 2. Try Secondary Failover: Groq Llama-3.3-70B
        if groq_ready:
            try:
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {Config.GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": Config.GROQ_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt + "\nRespond strictly in valid JSON format."},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"}
                }
                r = requests.post(url, headers=headers, json=payload, timeout=20)
                r.raise_for_status()
                raw_text = r.json()["choices"][0]["message"]["content"]
                mode_label = "Groq Llama-3.3-70B (Simulated Failover)" if Config.FORCE_GROQ_FAILOVER else "Groq Llama-3.3-70B (Auto-Failover)"
                return cls._extract_json(raw_text), mode_label
            except Exception as e:
                print(f"[Groq Failover Triggered] {e}")

        raise RuntimeError("No active LLM API keys responded. Please set a valid GEMINI_API_KEY or GROQ_API_KEY in .env.")

    @classmethod
    def analyze_image_forensics(
        cls,
        image_bytes: bytes,
        mime_type: str,
        context_note: str,
        face_crop_bytes: bytes = None
    ) -> dict:
        """
        Performs an unbiased multimodal deepfake & face-swap forensic inspection.
        Inspects both the full image and a zoomed-in Face ROI crop (if detected)
        and returns structured JSON with vision_risk_score (0-100) and report text.
        """
        if not cls._is_valid_key(Config.GEMINI_API_KEY):
            return {
                "vision_risk_score": None,
                "detected_category": "LOCAL_MATH_ONLY",
                "report_text": (
                    "Gemini API Key not configured for Vision pass. Relying on local Face-ROI "
                    "chrominance/frequency metrics, Error Level Analysis (ELA), and EXIF inspection."
                )
            }
        try:
            b64_img = base64.b64encode(image_bytes).decode("utf-8")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{Config.GEMINI_MODEL}:generateContent?key={Config.GEMINI_API_KEY}"

            prompt = (
                "You are an expert Digital Media & Deepfake Forensic Investigator. "
                "Critically examine the provided image (and the zoomed-in face crop if attached) "
                "for subtle synthetic manipulation. Do NOT assume the image is real just because the background is a broadcast studio. "
                "Specifically inspect for:\n"
                "1) FACE-SWAP / DEEPFAKE ARTIFACTS (e.g. FaceForensics++, DeepFaceLab, FaceSwap): "
                "Look closely at the inner face (eyes, nose, mustache, mouth, cheeks) versus the outer head (forehead, scalp, ears, neck, shirt collar). "
                "Check if the inner face appears slightly softer, blurrier, lower-resolution, waxier, or has a different skin-tone/lighting tint "
                "compared to the forehead, scalp, or sharp shirt collar. Check for blending mask seams around the eyebrows, cheekbones, or jawline, "
                "or unnatural mouth/mustache synthesis.\n"
                "2) GENERATIVE AI (DIFFUSION / GAN) ARTIFACTS: Overly airbrushed skin, asymmetrical pupils/teeth/ears, warped hands, or garbled text.\n"
                "3) DIGITAL SPLICING / CLONING: Pasted objects, lighting mismatches, or edge halos.\n\n"
                f"Local OpenCV Face-ROI & Sensor Telemetry (for reference only, do not let low compression scores override visual face-swap evidence): {context_note}\n\n"
                "Return strictly valid JSON with these exact keys:\n"
                "- 'vision_risk_score': Integer from 0 to 100 indicating probability of manipulation/deepfake "
                "(0-25 = genuine untouched photo/video frame; 45-65 = suspicious/heavily filtered/uncertain; 70-98 = likely face-swap deepfake, AI-generated, or spliced).\n"
                "- 'detected_category': One of ['FACE-SWAP / DEEPFAKE DETECTED', 'AI-GENERATED SYNTHETIC MEDIA', 'DIGITAL SPLICE / EDIT', 'AUTHENTIC / NO MANIPULATION DETECTED']\n"
                "- 'forensic_bullets': List of 4 detailed strings covering: (1) Facial Identity & Face-Swap Seam Analysis, "
                "(2) Inner-Face vs. Outer-Head Sharpness & Texture Consistency, (3) Splicing & Compression Profile, (4) Contextual & Provenance Assessment."
            )

            parts = [{"text": prompt}, {"inline_data": {"mime_type": mime_type, "data": b64_img}}]
            if face_crop_bytes:
                b64_face = base64.b64encode(face_crop_bytes).decode("utf-8")
                parts.append({"text": "ZOOMED-IN HIGH-RESOLUTION FACE & BOUNDARY CROP (Inspect inner face vs forehead/jawline/collar carefully):"})
                parts.append({"inline_data": {"mime_type": "image/jpeg", "data": b64_face}})

            payload = {
                "contents": [{"parts": parts}],
                "generationConfig": {
                    "temperature": 0.1,
                    "responseMimeType": "application/json"
                }
            }
            r = requests.post(url, json=payload, timeout=25)
            r.raise_for_status()
            raw_text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            parsed = cls._extract_json(raw_text)

            v_score = int(parsed.get("vision_risk_score", 30))
            category = parsed.get("detected_category", "FORENSIC AUDIT COMPLETE")
            bullets = parsed.get("forensic_bullets", [])
            if isinstance(bullets, list) and bullets:
                formatted_bullets = "\n".join([f"- {b}" for b in bullets])
            else:
                formatted_bullets = str(bullets)

            report_text = f"**Vision Forensic Classification:** `{category}` (Neural Deepfake Probability: **{v_score}%**)\n\n{formatted_bullets}"
            return {
                "vision_risk_score": v_score,
                "detected_category": category,
                "report_text": report_text
            }
        except Exception as e:
            return {
                "vision_risk_score": None,
                "detected_category": "VISION_ERROR_FALLBACK",
                "report_text": f"Vision API check encountered an error ({e}). Relying on local OpenCV Face-ROI, ELA, and EXIF metrics."
            }