import io
import hashlib
import numpy as np
import cv2
from PIL import Image, ImageChops, ImageEnhance, ExifTags
from core.llm_client import MultiModalLLMClient
from core.database import LiveAuditDatabase

class DeepfakeForensicsEngine:
    """
    Multimodal Synthetic Media, Face-Swap Deepfake & Splice Forensics Auditor:
      1. SHA-256 Cryptographic Provenance Hash
      2. EXIF & Software Signature Inspection (detects Photoshop, Midjourney, DALL-E, Canva, stripped headers)
      3. Patch-Aware Error Level Analysis (ELA) with CLAHE Visual Enhancement
      4. OpenCV Haar-Cascade Face-ROI Forensics (Forehead-to-Cheek YCrCb Skin-Masked CIE-LAB Seam Check,
         Inner-to-Outer Sharpness Drop Ratio, and 2D FFT Spectral Roll-off)
      5. Multimodal Vision Deepfake Auditor (Full Frame + Zoomed Face Crop) with Vision-Guided Fusion
    """

    @staticmethod
    def extract_exif_metadata(pil_img: Image.Image) -> dict:
        metadata = {
            "format": pil_img.format or "Unknown",
            "mode": pil_img.mode,
            "resolution": f"{pil_img.width}x{pil_img.height}",
            "exif_present": False,
            "software_signature": "None Detected",
            "camera_model": "None Detected",
            "suspicious_flags": []
        }
        try:
            exif_data = pil_img.getexif()
            if exif_data:
                metadata["exif_present"] = True
                for tag_id, value in exif_data.items():
                    tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                    val_str = str(value)[:120]
                    if tag_name in ("Software", "ProcessingSoftware", "HostComputer"):
                        metadata["software_signature"] = val_str
                    elif tag_name in ("Make", "Model"):
                        metadata["camera_model"] = val_str
                    elif tag_name in ("DateTime", "DateTimeOriginal"):
                        metadata["timestamp"] = val_str

            info_str = " ".join([f"{k}:{v}" for k, v in pil_img.info.items() if isinstance(v, (str, bytes))])
            ai_keywords = [
                "midjourney", "stable diffusion", "dall-e", "firefly", "comfyui",
                "automatic1111", "photoshop", "gimp", "canva", "deepfake", "faceswap"
            ]
            combined_check = (metadata["software_signature"] + " " + info_str).lower()
            for kw in ai_keywords:
                if kw in combined_check:
                    metadata["suspicious_flags"].append(f"Editing/AI signature detected: '{kw.upper()}'")

            if not metadata["exif_present"]:
                metadata["suspicious_flags"].append("EXIF camera metadata stripped (common in social media forwards & AI generations)")
        except Exception as e:
            metadata["suspicious_flags"].append(f"EXIF parse warning: {e}")

        return metadata

    @staticmethod
    def analyze_face_swap_roi(rgb_np: np.ndarray, ela_diff_np: np.ndarray) -> dict:
        """
        Detects faces using OpenCV Haar Cascades and measures localized Face-Swap anomalies
        without false-triggering on studio background walls:
          - Skin-Masked Forehead vs. Inner-Cheek CIE-LAB Chrominance Shift (excludes background walls)
          - Inner-Face vs. Forehead/Outer-Head Sharpness Ratio (detects autoencoder blur inside face mask)
          - 2D FFT High-Frequency Energy Roll-off inside the face core
          - Edge-Normalized Face ELA vs. Context ELA Ratio
        """
        gray = cv2.cvtColor(rgb_np, cv2.COLOR_RGB2GRAY)
        h_img, w_img = gray.shape

        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        face_cascade = cv2.CascadeClassifier(cascade_path)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(35, 35))

        if len(faces) == 0:
            alt_path = cv2.data.haarcascades + "haarcascade_frontalface_alt2.xml"
            alt_cascade = cv2.CascadeClassifier(alt_path)
            if not alt_cascade.empty():
                faces = alt_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(35, 35))

        if len(faces) == 0:
            return {"face_detected": False, "face_anomaly_score": 0.0, "face_crop_bytes": None, "face_box": None, "flags": []}

        # Select primary (largest) face
        faces = sorted(faces, key=lambda b: b[2] * b[3], reverse=True)
        x, y, w, h = [int(v) for v in faces[0]]

        # 1. Inner Face Core (central 56% where FaceSwap blends synthesized mask)
        ix1 = x + int(w * 0.22)
        iy1 = y + int(h * 0.24)
        ix2 = x + int(w * 0.78)
        iy2 = y + int(h * 0.80)

        # 2. Expanded Context Box for Vision Crop (includes forehead, scalp border, jawline, and collar)
        ox1 = max(0, x - int(w * 0.25))
        oy1 = max(0, y - int(h * 0.25))
        ox2 = min(w_img, x + w + int(w * 0.25))
        oy2 = min(h_img, y + h + int(h * 0.30))

        inner_gray = gray[iy1:iy2, ix1:ix2]
        inner_lap_var = float(cv2.Laplacian(inner_gray, cv2.CV_64F).var()) if inner_gray.size > 0 else 80.0

        # Compare Inner-Face sharpness against Upper Forehead/Temple strip (never hits background wall)
        fh_x1, fh_x2 = x + int(w * 0.28), x + int(w * 0.72)
        fh_y1, fh_y2 = y + int(h * 0.05), y + int(h * 0.22)
        forehead_gray = gray[fh_y1:fh_y2, fh_x1:fh_x2]
        forehead_lap_var = float(cv2.Laplacian(forehead_gray, cv2.CV_64F).var()) if forehead_gray.size > 0 else inner_lap_var

        # Sharpness drop ratio: < 0.52 means inner face is noticeably softer/blurrier than forehead
        sharpness_ratio = inner_lap_var / (forehead_lap_var + 15.0)

        # Skin-Only CIE-LAB Chrominance comparison (uses YCrCb skin mask so blue/dark studio walls are excluded)
        ycrcb = cv2.cvtColor(rgb_np, cv2.COLOR_RGB2YCrCb)
        skin_mask = (
            (ycrcb[:, :, 1] >= 133) & (ycrcb[:, :, 1] <= 178) &
            (ycrcb[:, :, 2] >= 75) & (ycrcb[:, :, 2] <= 130)
        )

        lab_img = cv2.cvtColor(rgb_np, cv2.COLOR_RGB2LAB).astype(np.float32)

        # Inner cheek/nose skin region (excludes open mouth at bottom)
        cheek_y1, cheek_y2 = y + int(h * 0.30), y + int(h * 0.62)
        cheek_x1, cheek_x2 = x + int(w * 0.26), x + int(w * 0.74)
        inner_skin_mask = np.zeros_like(gray, dtype=bool)
        inner_skin_mask[cheek_y1:cheek_y2, cheek_x1:cheek_x2] = True
        inner_skin_mask = inner_skin_mask & skin_mask

        # Forehead skin region (above the face-swap mask seam, strictly inside head width)
        outer_skin_mask = np.zeros_like(gray, dtype=bool)
        outer_skin_mask[fh_y1:fh_y2, fh_x1:fh_x2] = True
        outer_skin_mask = outer_skin_mask & skin_mask

        if np.sum(inner_skin_mask) >= 25 and np.sum(outer_skin_mask) >= 20:
            inner_a = float(np.mean(lab_img[inner_skin_mask, 1]))
            inner_b = float(np.mean(lab_img[inner_skin_mask, 2]))
            outer_a = float(np.mean(lab_img[outer_skin_mask, 1]))
            outer_b = float(np.mean(lab_img[outer_skin_mask, 2]))
            chroma_shift = float(np.hypot(inner_a - outer_a, inner_b - outer_b))
        else:
            chroma_shift = 1.5

        # 2D FFT High-Frequency Spectral Ratio on Inner Face
        fft_f = np.fft.fftshift(np.fft.fft2(inner_gray.astype(np.float32)))
        mag_spec = np.log1p(np.abs(fft_f))
        fh_s, fw_s = mag_spec.shape
        cy, cx = fh_s // 2, fw_s // 2
        Y, X = np.ogrid[:fh_s, :fw_s]
        dist = np.hypot(X - cx, Y - cy)
        max_r = max(1.0, min(fh_s, fw_s) / 2.0)
        high_freq_mask = dist > (0.45 * max_r)
        hf_energy_ratio = float(np.mean(mag_spec[high_freq_mask]) / (np.mean(mag_spec) + 1e-5))

        # Inner-Face ELA vs Head-Context ELA (prevents smooth studio walls from inflating ratio)
        face_ela = float(np.mean(ela_diff_np[iy1:iy2, ix1:ix2]))
        context_ela = float(np.mean(ela_diff_np[oy1:oy2, ox1:ox2])) + 0.5
        face_ela_ratio = face_ela / context_ela

        # Calculate calibrated mathematical anomaly score (0 for crisp authentic faces)
        face_anomaly = 0.0
        flags = []

        # Signal A: Inner face is unnaturally blurred (low absolute Laplacian OR sharp drop vs forehead)
        if inner_lap_var < 65.0:
            blur_pen = min(38.0, (65.0 - inner_lap_var) * 0.85)
            face_anomaly += blur_pen
            flags.append(f"Inner-face neural smoothing detected (Face Laplacian={inner_lap_var:.1f})")
        elif sharpness_ratio < 0.52 and inner_lap_var < 160.0:
            blur_pen = min(30.0, (0.52 - sharpness_ratio) * 90.0)
            face_anomaly += blur_pen
            flags.append(f"Inner-face vs. forehead sharpness drop (Ratio={sharpness_ratio:.2f})")

        # Signal B: True skin-to-skin chrominance shift between forehead and inner cheek
        if chroma_shift > 5.8:
            chroma_pen = min(32.0, (chroma_shift - 5.2) * 5.5)
            face_anomaly += chroma_pen
            flags.append(f"Forehead-to-cheek skin-tone seam shift (CIE-LAB ΔChroma={chroma_shift:.2f})")

        # Signal C: Steep FFT high-frequency roll-off in face core (only when face is not crisp)
        if hf_energy_ratio < 0.73 and inner_lap_var < 150.0:
            fft_pen = min(25.0, (0.73 - hf_energy_ratio) * 180.0)
            face_anomaly += fft_pen
            flags.append(f"Face 2D-FFT high-frequency spectral roll-off ({hf_energy_ratio:.2f})")

        # Signal D: Inner-face vs Head-Context ELA compression mismatch
        if face_ela_ratio > 1.55:
            ela_face_pen = min(25.0, (face_ela_ratio - 1.45) * 40.0)
            face_anomaly += ela_face_pen
            flags.append(f"Localized inner-face compression mismatch (Inner/Context ELA={face_ela_ratio:.2f}x)")

        face_anomaly_score = min(96.0, round(face_anomaly, 1))

        # Crop zoomed-in high-res face patch for Gemini Vision inspection
        crop_rgb = rgb_np[oy1:oy2, ox1:ox2]
        crop_pil = Image.fromarray(crop_rgb)
        crop_buf = io.BytesIO()
        crop_pil.save(crop_buf, format="JPEG", quality=95)

        return {
            "face_detected": True,
            "face_box": (x, y, w, h),
            "inner_box": (ix1, iy1, ix2, iy2),
            "inner_lap_var": round(inner_lap_var, 2),
            "sharpness_ratio": round(sharpness_ratio, 2),
            "chroma_shift": round(chroma_shift, 2),
            "hf_energy_ratio": round(hf_energy_ratio, 3),
            "face_ela_ratio": round(face_ela_ratio, 2),
            "face_anomaly_score": face_anomaly_score,
            "face_crop_bytes": crop_buf.getvalue(),
            "flags": flags
        }

    @classmethod
    def compute_ela_heatmap(cls, pil_img: Image.Image, quality: int = 90) -> tuple[Image.Image, float, float, dict]:
        rgb_img = pil_img.convert("RGB")
        rgb_np = np.array(rgb_img)

        buffer = io.BytesIO()
        rgb_img.save(buffer, "JPEG", quality=quality)
        buffer.seek(0)
        resaved_img = Image.open(buffer)

        ela_diff = ImageChops.difference(rgb_img, resaved_img)
        diff_np = np.asarray(ela_diff, dtype=np.float32)

        h, w, _ = diff_np.shape
        patch_size = max(16, min(h, w) // 12)
        patch_means = []
        for py in range(0, h - patch_size + 1, patch_size):
            for px in range(0, w - patch_size + 1, patch_size):
                patch_means.append(float(np.mean(diff_np[py:py+patch_size, px:px+patch_size])))

        p99_diff = float(np.percentile(diff_np, 99))
        if patch_means:
            p95_patch = float(np.percentile(patch_means, 95))
            median_patch = float(np.median(patch_means)) + 1.2
            patch_ratio = p95_patch / median_patch
        else:
            patch_ratio = 1.0

        base_ela = (p99_diff / 42.0) * 55.0
        patch_boost = max(0.0, (patch_ratio - 2.4) * 10.0)
        ela_anomaly_score = min(100.0, round(base_ela + patch_boost, 1))

        # Enhance ELA visual heatmap using CLAHE
        extrema = ela_diff.getextrema()
        max_diff = max([ex[1] for ex in extrema]) or 1
        scale = 255.0 / max_diff
        ela_amplified = np.array(ImageEnhance.Brightness(ela_diff).enhance(scale))

        lab_ela = cv2.cvtColor(ela_amplified, cv2.COLOR_RGB2LAB)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        lab_ela[:, :, 0] = clahe.apply(lab_ela[:, :, 0])
        ela_visual_np = cv2.cvtColor(lab_ela, cv2.COLOR_LAB2RGB)

        # Run localized Face-Swap ROI Forensics
        face_info = cls.analyze_face_swap_roi(rgb_np, diff_np)

        if face_info["face_detected"]:
            fx, fy, fw, fh = face_info["face_box"]
            ix1, iy1, ix2, iy2 = face_info["inner_box"]
            cv2.rectangle(ela_visual_np, (fx, fy), (fx + fw, fy + fh), (56, 189, 248), 2)
            cv2.rectangle(ela_visual_np, (ix1, iy1), (ix2, iy2), (244, 63, 94), 1)

        ela_visual = Image.fromarray(ela_visual_np)

        gray_np = cv2.cvtColor(rgb_np, cv2.COLOR_RGB2GRAY)
        global_lap_var = float(cv2.Laplacian(gray_np, cv2.CV_64F).var())
        effective_noise_var = face_info["inner_lap_var"] if face_info["face_detected"] else round(global_lap_var, 2)

        return ela_visual, ela_anomaly_score, effective_noise_var, face_info

    @classmethod
    def audit_image(cls, image_bytes: bytes, filename: str, db: LiveAuditDatabase) -> dict:
        sha256_hash = hashlib.sha256(image_bytes).hexdigest()
        pil_img = Image.open(io.BytesIO(image_bytes))
        mime_type = f"image/{(pil_img.format or 'jpeg').lower()}"

        metadata = cls.extract_exif_metadata(pil_img)
        ela_img, ela_score, noise_variance, face_info = cls.compute_ela_heatmap(pil_img)

        # 1. Calculate local mathematical manipulation risk
        math_risk = ela_score * 0.35
        if face_info["face_detected"]:
            math_risk = max(math_risk, face_info["face_anomaly_score"] * 0.75 + ela_score * 0.20)

        has_ai_exif = any("Editing/AI signature" in f for f in metadata["suspicious_flags"])
        if has_ai_exif:
            math_risk += 35.0
        if not metadata["exif_present"]:
            math_risk += 6.0
        if noise_variance < 50.0:
            math_risk += 15.0
            metadata["suspicious_flags"].append(
                f"Low high-frequency surface detail (Laplacian var={noise_variance}) — typical of neural synthesis"
            )

        # 2. Run Multimodal Vision Deepfake & Face-Swap Pass
        if face_info["face_detected"]:
            context_note = (
                f"Face Detected: Yes | Inner-Face Laplacian Sharpness: {face_info['inner_lap_var']} | "
                f"Forehead-to-Cheek Skin Chroma Shift: {face_info['chroma_shift']} | "
                f"2D-FFT High-Freq Ratio: {face_info['hf_energy_ratio']} | "
                f"Inner/Context ELA Ratio: {face_info['face_ela_ratio']}x | "
                f"EXIF Present: {metadata['exif_present']}"
            )
        else:
            context_note = (
                f"Face Detected: No | Global Laplacian Variance: {noise_variance} | "
                f"EXIF Present: {metadata['exif_present']} | Flags: {metadata['suspicious_flags']}"
            )

        vision_res = MultiModalLLMClient.analyze_image_forensics(
            image_bytes=image_bytes,
            mime_type=mime_type,
            context_note=context_note,
            face_crop_bytes=face_info.get("face_crop_bytes")
        )
        vision_score = vision_res.get("vision_risk_score")
        vision_report = vision_res.get("report_text", "")
        vision_category = str(vision_res.get("detected_category", "")).upper()

        # 3. Vision-Guided Forensic Fusion (Prevents false-positive math flags from overriding authentic Vision verdicts)
        if vision_score is not None:
            v_float = float(vision_score)
            if v_float >= 55.0 or "DEEPFAKE" in vision_category or "SYNTHETIC" in vision_category or "SPLICE" in vision_category:
                # Multimodal Vision detected manipulation/deepfake: boost risk score into High Risk range
                if face_info["flags"]:
                    metadata["suspicious_flags"].extend(face_info["flags"])
                metadata["suspicious_flags"].append(
                    f"Multimodal Vision flagged '{vision_category}' ({int(v_float)}% neural risk)"
                )
                fused_risk = max(v_float, 0.75 * v_float + 0.25 * math_risk)
                displayed_ela_score = round(max(ela_score, face_info.get("face_anomaly_score", 0.0), v_float * 0.85), 1)
            elif v_float <= 35.0 and not has_ai_exif:
                # Multimodal Vision confirmed AUTHENTIC media (e.g. 15%): trust Vision & suppress noisy background flags
                fused_risk = 0.75 * v_float + 0.25 * min(math_risk, 32.0)
                displayed_ela_score = round(min(ela_score, 28.0), 1)
            else:
                if face_info["flags"]:
                    metadata["suspicious_flags"].extend(face_info["flags"])
                fused_risk = 0.65 * v_float + 0.35 * math_risk
                displayed_ela_score = round(max(ela_score, face_info.get("face_anomaly_score", 0.0)), 1)
        else:
            if face_info["flags"]:
                metadata["suspicious_flags"].extend(face_info["flags"])
            fused_risk = math_risk
            displayed_ela_score = round(max(ela_score, face_info.get("face_anomaly_score", 0.0)), 1)

        risk_score = min(99.0, max(5.0, round(fused_risk, 1)))

        if risk_score >= 60:
            verdict = "HIGH MANIPULATION / DEEPFAKE RISK"
        elif risk_score >= 38:
            verdict = "MODERATE ANOMALY / SUSPICIOUS EDIT OR RECOMPRESSION"
        else:
            verdict = "LOW ANOMALY / CONSISTENT AUTHENTIC MEDIA"

        db.save_media_audit(
            filename=filename,
            sha256_hash=sha256_hash,
            ela_score=risk_score,
            verdict=verdict,
            metadata=metadata,
            vision_analysis=vision_report
        )

        return {
            "filename": filename,
            "sha256_hash": sha256_hash,
            "original_image": pil_img,
            "ela_image": ela_img,
            "ela_score": displayed_ela_score,
            "noise_variance": noise_variance,
            "risk_score": risk_score,
            "verdict": verdict,
            "metadata": metadata,
            "vision_report": vision_report
        }