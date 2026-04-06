from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

import shutil
import time
import base64
import cv2
import numpy as np
from uuid import uuid4
from pathlib import Path

from auth.dependencies import get_current_user
from database.db import get_db
from database.crud import create_analysis_case
from api.schemas import AnalysisCaseCreate

from ml.model_a.predict import predict_idc
from ml.model_a.gradcam import generate_gradcam

from ml.model_b.nusec_inference import predict_nusec_from_path
from ml.model_b.midesec_inference import MiDeSeCB2Predictor
from ml.model_b.model_b_fusion import build_model_b_interpretation

router = APIRouter()

# Backend root folder
BASE_DIR = Path(__file__).resolve().parents[2]

# =========================
# MODEL A STORAGE
# =========================
ORIGINALS_DIR = BASE_DIR / "storage" / "analysis" / "originals"
OVERLAYS_DIR = BASE_DIR / "storage" / "analysis" / "overlays"
HEATMAPS_DIR = BASE_DIR / "storage" / "analysis" / "heatmaps"

ORIGINALS_DIR.mkdir(parents=True, exist_ok=True)
OVERLAYS_DIR.mkdir(parents=True, exist_ok=True)
HEATMAPS_DIR.mkdir(parents=True, exist_ok=True)

# =========================
# MODEL B STORAGE
# =========================
MODEL_B_B1_DIR = BASE_DIR / "storage" / "analysis" / "model_b" / "b1"
MODEL_B_B2_DIR = BASE_DIR / "storage" / "analysis" / "model_b" / "b2"
MODEL_B_B1_MASKS_DIR = BASE_DIR / "storage" / "analysis" / "model_b" / "b1_masks"
MODEL_B_B2_MASKS_DIR = BASE_DIR / "storage" / "analysis" / "model_b" / "b2_masks"
MODEL_B_B1_OVERLAYS_DIR = BASE_DIR / "storage" / "analysis" / "model_b" / "b1_overlays"
MODEL_B_B2_OVERLAYS_DIR = BASE_DIR / "storage" / "analysis" / "model_b" / "b2_overlays"

MODEL_B_B1_DIR.mkdir(parents=True, exist_ok=True)
MODEL_B_B2_DIR.mkdir(parents=True, exist_ok=True)
MODEL_B_B1_MASKS_DIR.mkdir(parents=True, exist_ok=True)
MODEL_B_B2_MASKS_DIR.mkdir(parents=True, exist_ok=True)
MODEL_B_B1_OVERLAYS_DIR.mkdir(parents=True, exist_ok=True)
MODEL_B_B2_OVERLAYS_DIR.mkdir(parents=True, exist_ok=True)

# =========================
# MODEL B2 LOADER
# =========================
B2_MODEL_PATH = BASE_DIR / "ml" / "model_b" / "runs" / "midesec_b2" / "best_model.pth"
_b2_predictor = None


def get_b2_predictor():
    global _b2_predictor

    if _b2_predictor is None:
        if not B2_MODEL_PATH.exists():
            raise FileNotFoundError(f"MiDeSeC B2 model not found: {B2_MODEL_PATH}")
        _b2_predictor = MiDeSeCB2Predictor(model_path=B2_MODEL_PATH)

    return _b2_predictor


def save_upload_file(upload_file: UploadFile, save_dir: Path, prefix: str):
    file_extension = Path(upload_file.filename).suffix if upload_file.filename else ".png"
    filename = f"{prefix}{file_extension}"
    full_path = save_dir / filename

    with open(full_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    return filename, full_path


def to_base64_image(image_data):
    if image_data is None:
        return None

    if isinstance(image_data, str):
        return image_data

    success, buffer = cv2.imencode(".png", image_data)
    if not success:
        return None
    return base64.b64encode(buffer).decode("utf-8")


def save_output_image(image_data, save_path: Path):
    if image_data is None:
        return None

    if isinstance(image_data, str):
        try:
            img_bytes = base64.b64decode(image_data)
            np_arr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_UNCHANGED)
            if img is None:
                return None
            cv2.imwrite(str(save_path), img)
            return True
        except Exception:
            return None

    cv2.imwrite(str(save_path), image_data)
    return True


@router.post("/predict")
async def predict(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    start_time = time.time()

    file_extension = Path(file.filename).suffix if file.filename else ".png"
    unique_id = str(uuid4())

    original_filename = f"{unique_id}{file_extension}"
    original_full_path = ORIGINALS_DIR / original_filename
    original_db_path = f"storage/analysis/originals/{original_filename}"

    with open(original_full_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        prediction, confidence = predict_idc(str(original_full_path))
        confidence_val = float(confidence)
        final_prediction = prediction

        if confidence_val < 0.65:
            note = "Low confidence prediction"
        else:
            note = "High confidence prediction"

        heatmap_base64 = None
        overlay_base64 = None
        heatmap_db_path = None
        overlay_db_path = None
        raw_heatmap_db_path = None

        if final_prediction == "IDC":
            gradcam_result = generate_gradcam(str(original_full_path))

            heatmap = gradcam_result["heatmap"]
            overlay = gradcam_result["overlay"]

            heatmap_filename = f"{unique_id}_heatmap.png"
            heatmap_full_path = HEATMAPS_DIR / heatmap_filename
            cv2.imwrite(str(heatmap_full_path), heatmap)
            raw_heatmap_db_path = f"storage/analysis/heatmaps/{heatmap_filename}"

            overlay_filename = f"{unique_id}_overlay.png"
            overlay_full_path = OVERLAYS_DIR / overlay_filename
            cv2.imwrite(str(overlay_full_path), overlay)
            overlay_db_path = f"storage/analysis/overlays/{overlay_filename}"

            heatmap_db_path = overlay_db_path

            _, heatmap_buffer = cv2.imencode(".png", heatmap)
            heatmap_base64 = base64.b64encode(heatmap_buffer).decode("utf-8")

            _, overlay_buffer = cv2.imencode(".png", overlay)
            overlay_base64 = base64.b64encode(overlay_buffer).decode("utf-8")

        end_time = time.time()
        inference_time_val = round(end_time - start_time, 2)

        case_data = AnalysisCaseCreate(
            user_id=current_user.id,
            model_type="model_a",
            image_path=original_db_path,
            prediction_label=final_prediction,
            confidence=round(confidence_val, 2),
            result_status="completed",
            heatmap_path=heatmap_db_path,
            inference_time=inference_time_val,
            extra_data={
                "model_name": "ResNet-18",
                "note": note,
                "original_filename": file.filename,
                "overlay_path": overlay_db_path,
                "raw_heatmap_path": raw_heatmap_db_path
            }
        )

        saved_case = create_analysis_case(db, case_data)

        return {
            "case_id": saved_case.id,
            "prediction": final_prediction,
            "confidence": round(confidence_val, 2),
            "model": "ResNet-18",
            "note": note,
            "inference_time": inference_time_val,
            "heatmap": heatmap_base64,
            "overlay": overlay_base64,
            "image_path": original_db_path,
            "overlay_path": overlay_db_path,
            "raw_heatmap_path": raw_heatmap_db_path
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.post("/predict/model-b")
async def predict_model_b(
    b1_image: UploadFile = File(...),
    b2_image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    start_time = time.time()
    unique_id = str(uuid4())

    try:
        # =========================
        # SAVE BOTH INPUT IMAGES
        # =========================
        b1_filename, b1_full_path = save_upload_file(
            b1_image,
            MODEL_B_B1_DIR,
            f"{unique_id}_b1"
        )
        b2_filename, b2_full_path = save_upload_file(
            b2_image,
            MODEL_B_B2_DIR,
            f"{unique_id}_b2"
        )

        b1_db_path = f"storage/analysis/model_b/b1/{b1_filename}"
        b2_db_path = f"storage/analysis/model_b/b2/{b2_filename}"

        # =========================
        # RUN B1 / B2 INFERENCE
        # =========================
        b1_raw_result = predict_nusec_from_path(str(b1_full_path))

        b2_predictor = get_b2_predictor()
        b2_raw_result = b2_predictor.predict_from_path(str(b2_full_path))

        b1_findings = dict(b1_raw_result.get("findings", {}))
        b2_findings = dict(b2_raw_result.get("findings", {}))

        # normalize key for fusion
        if "mitotic_activity" not in b2_findings and "mitotic_activity_level" in b2_findings:
            b2_findings["mitotic_activity"] = b2_findings["mitotic_activity_level"]

        b1_mask = b1_raw_result.get("mask")
        b1_overlay = b1_raw_result.get("overlay")

        b2_mask = b2_raw_result.get("mask")
        b2_overlay = b2_raw_result.get("overlay")

        # NuSeC overlay RGB se aata hai, OpenCV save/encode ke liye BGR kar do
        if isinstance(b1_overlay, np.ndarray) and len(b1_overlay.shape) == 3 and b1_overlay.shape[2] == 3:
            b1_overlay = cv2.cvtColor(b1_overlay, cv2.COLOR_RGB2BGR)

        # =========================
        # SAVE MODEL B OUTPUTS
        # =========================
        b1_mask_filename = f"{unique_id}_b1_mask.png"
        b1_overlay_filename = f"{unique_id}_b1_overlay.png"
        b2_mask_filename = f"{unique_id}_b2_mask.png"
        b2_overlay_filename = f"{unique_id}_b2_overlay.png"

        b1_mask_full_path = MODEL_B_B1_MASKS_DIR / b1_mask_filename
        b1_overlay_full_path = MODEL_B_B1_OVERLAYS_DIR / b1_overlay_filename
        b2_mask_full_path = MODEL_B_B2_MASKS_DIR / b2_mask_filename
        b2_overlay_full_path = MODEL_B_B2_OVERLAYS_DIR / b2_overlay_filename

        save_output_image(b1_mask, b1_mask_full_path)
        save_output_image(b1_overlay, b1_overlay_full_path)
        save_output_image(b2_mask, b2_mask_full_path)
        save_output_image(b2_overlay, b2_overlay_full_path)

        b1_mask_db_path = f"storage/analysis/model_b/b1_masks/{b1_mask_filename}"
        b1_overlay_db_path = f"storage/analysis/model_b/b1_overlays/{b1_overlay_filename}"
        b2_mask_db_path = f"storage/analysis/model_b/b2_masks/{b2_mask_filename}"
        b2_overlay_db_path = f"storage/analysis/model_b/b2_overlays/{b2_overlay_filename}"

        # =========================
        # COMBINED INTERPRETATION
        # =========================
        combined_result = build_model_b_interpretation(
            b1_findings,
            b2_findings
        )

        end_time = time.time()
        inference_time_val = round(end_time - start_time, 2)

        # =========================
        # SAVE ONE COMBINED CASE
        # =========================
        case_data = AnalysisCaseCreate(
            user_id=current_user.id,
            model_type="model_b",
            image_path=b1_db_path,
            prediction_label=combined_result.get("grade_support", "Model B analysis complete"),
            confidence=0.0,
            result_status="completed",
            heatmap_path=b1_overlay_db_path,
            inference_time=inference_time_val,
            extra_data={
                "model_name": "Model B Combined",
                "b1_original_filename": b1_image.filename,
                "b2_original_filename": b2_image.filename,
                "b1_image_path": b1_db_path,
                "b2_image_path": b2_db_path,
                "b1_result": {
                    "label": "Nuclei Analysis",
                    "findings": b1_findings,
                    "mask_path": b1_mask_db_path,
                    "overlay_path": b1_overlay_db_path
                },
                "b2_result": {
                    "label": "Mitosis Analysis",
                    "findings": b2_findings,
                    "mask_path": b2_mask_db_path,
                    "overlay_path": b2_overlay_db_path
                },
                "combined_result": combined_result
            }
        )

        saved_case = create_analysis_case(db, case_data)

        return {
            "success": True,
            "case_id": saved_case.id,
            "model": "Model B",
            "inference_time": inference_time_val,
            "b1_result": {
                "label": "Nuclei Analysis",
                "findings": b1_findings,
                "mask": to_base64_image(b1_mask),
                "overlay": to_base64_image(b1_overlay),
                "mask_path": b1_mask_db_path,
                "overlay_path": b1_overlay_db_path
            },
            "b2_result": {
                "label": "Mitosis Analysis",
                "findings": b2_findings,
                "mask": to_base64_image(b2_mask),
                "overlay": to_base64_image(b2_overlay),
                "mask_path": b2_mask_db_path,
                "overlay_path": b2_overlay_db_path
            },
            "combined_result": combined_result,
            "b1_image_path": b1_db_path,
            "b2_image_path": b2_db_path
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model B prediction failed: {str(e)}")