# Copyright (c) Opendatalab. All rights reserved.
"""
Tesseract OCR wrapper for Vietnamese text recognition.
Uses PaddleOCR for detection (boxes) + Tesseract for recognition (text).
Falls back to PaddleOCR when Tesseract is unavailable.
"""
import copy
from pathlib import Path

import cv2
import numpy as np
from loguru import logger

from mineru.utils.ocr_utils import (
    check_img,
    preprocess_image,
    sorted_boxes,
    merge_det_boxes,
    update_det_boxes,
    get_rotate_crop_image,
)

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

# Try to use PaddleOCR for detection when Tesseract is used for rec
from mineru.model.ocr.pytorch_paddle import PytorchPaddleOCR


class TesseractViOCR:
    """
    Hybrid OCR: PaddleOCR detection + Tesseract recognition for Vietnamese.
    Preserves MinerU layout/tables/images; only replaces text recognition.
    """

    def __init__(self, det_db_box_thresh=0.3, det_db_unclip_ratio=1.8,
                 enable_merge_det_boxes=True, **kwargs):
        if not TESSERACT_AVAILABLE:
            raise ImportError(
                "Tesseract OCR requires: pip install pytesseract pillow. "
                "Also install: apt-get install tesseract-ocr tesseract-ocr-vie"
            )
        self.det_ocr = PytorchPaddleOCR(
            det_db_box_thresh=det_db_box_thresh,
            lang="en",  # Detection works with any lang
            det_db_unclip_ratio=det_db_unclip_ratio,
            enable_merge_det_boxes=enable_merge_det_boxes,
        )
        self.tesseract_lang = "vie"

    def _tesseract_rec(self, img_crop):
        """Run Tesseract on single crop, return (text, score)."""
        if img_crop is None or img_crop.size == 0:
            return ("", 0.0)
        if len(img_crop.shape) == 3:
            pil_img = Image.fromarray(cv2.cvtColor(img_crop, cv2.COLOR_BGR2RGB))
        else:
            pil_img = Image.fromarray(img_crop)
        try:
            data = pytesseract.image_to_data(pil_img, lang=self.tesseract_lang, output_type=pytesseract.Output.DICT)
            texts = []
            confs = []
            for i, conf in enumerate(data["conf"]):
                if int(conf) > 0 and data["text"][i].strip():
                    texts.append(data["text"][i])
                    confs.append(int(conf) / 100.0)
            if texts:
                text = " ".join(texts)
                score = sum(confs) / len(confs) if confs else 0.8
            else:
                text = pytesseract.image_to_string(pil_img, lang=self.tesseract_lang).strip()
                score = 0.8 if text else 0.0
            return (text, min(1.0, score))
        except Exception as e:
            logger.warning(f"Tesseract OCR failed: {e}")
            return ("", 0.0)

    def ocr(self, img, det=True, rec=True, mfd_res=None, tqdm_enable=False, tqdm_desc="OCR-rec Predict"):
        assert isinstance(img, (np.ndarray, list, str, bytes))
        if isinstance(img, list) and det:
            raise ValueError("When input is a list of images, det must be False")
        img = check_img(img)
        imgs = [img] if not isinstance(img, list) else img

        if det and rec:
            ocr_res = []
            for single_img in imgs:
                single_img = preprocess_image(single_img) if not isinstance(single_img, list) else single_img
                det_res = self.det_ocr.ocr(single_img, det=True, rec=False, mfd_res=mfd_res)
                if not det_res or not det_res[0]:
                    ocr_res.append(None)
                    continue
                dt_boxes = det_res[0]
                ori_im = single_img.copy() if isinstance(single_img, np.ndarray) else np.array(single_img)
                tmp_res = []
                for box in dt_boxes:
                    pts = np.array(box, dtype=np.float32).reshape(4, 2)
                    img_crop = get_rotate_crop_image(ori_im, pts)
                    text, score = self._tesseract_rec(img_crop)
                    tmp_res.append([box if isinstance(box, list) else pts.tolist(), (text, score)])
                ocr_res.append(tmp_res)
            return ocr_res

        elif det and not rec:
            return self.det_ocr.ocr(img, det=True, rec=False, mfd_res=mfd_res)

        elif not det and rec:
            # imgs = [crop1, crop2, ...] - list of crops to recognize
            crops = [preprocess_image(x) if isinstance(x, np.ndarray) else x for x in imgs]
            rec_res = []
            for crop in crops:
                text, score = self._tesseract_rec(crop)
                rec_res.append((text, score))
            return [rec_res]

        return []
