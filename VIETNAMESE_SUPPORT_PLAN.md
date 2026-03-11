# Plan: Add Vietnamese Language Support to MinerU

## Current State Analysis

### What Already Works
- **`mineru/model/ocr/pytorch_paddle.py`**: `"vi"` is in `latin_lang` list (line 62) → maps to `"latin"` OCR model ✓
- **`projects/mcp/src/mineru/language.py`**: Vietnamese (`"vi"`) is in MCP language list ✓
- **Pipeline OCR**: Uses PaddleOCR's `latin` model, which includes Vietnamese in its character set

### What's Broken or Missing
1. **CLI** (`mineru/cli/client.py`): `--lang` uses `click.Choice()` that does NOT include `"vi"` — users must guess to use `"latin"`
2. **Gradio** (`mineru/cli/gradio_app.py`): Vietnamese is buried in the long "latin" dropdown description — no prominent Vietnamese option
3. **FastAPI** (`mineru/cli/fast_api.py`): Documentation mentions Vietnamese only inside the "latin" description
4. **Hybrid backend** (`mineru/backend/hybrid/hybrid_analyze.py`): `_should_enable_vlm_ocr()` only enables VLM OCR for `["ch", "en"]` — Vietnamese uses pipeline OCR only (lower accuracy path)
5. **Post-processing** (`vlm_middle_json_mkcontent.py`, `pipeline_middle_json_mkcontent.py`): `cjk_langs = {'zh', 'ja', 'ko'}` — Vietnamese gets Western text handling (adds spaces). This is correct since Vietnamese uses spaces between words.

---

## Implementation Plan

### Phase 1: Explicit Vietnamese UX (Required)

| # | Task | File(s) | Change |
|---|------|---------|--------|
| 1.1 | Add `"vi"` to CLI language choices | `mineru/cli/client.py` | Add `'vi'` to `click.Choice([...])` for `--lang` (line ~76) |
| 1.2 | Add prominent Vietnamese option to Gradio | `mineru/cli/gradio_app.py` | Add `'vi (Vietnamese)'` to `other_lang` list so it appears as a top-level option |
| 1.3 | Update FastAPI docs | `mineru/cli/fast_api.py` | Add `- vi: Vietnamese` to the `lang_list` Form description |
| 1.4 | Verify OCR mapping | `mineru/model/ocr/pytorch_paddle.py` | Confirm `"vi"` in `latin_lang` (already present) — no change needed |

**Result**: Users can explicitly select `-l vi` (CLI), "vi (Vietnamese)" (Gradio), or `"vi"` (API).

---

### Phase 2: Hybrid Backend VLM OCR (Optional — Investigate First)

| # | Task | File(s) | Change |
|---|------|---------|--------|
| 2.1 | Check VLM model language support | MinerU VLM model docs / config | Determine if the VLM (e.g., MinerU2.5) supports Vietnamese OCR. If yes, add `"vi"` or `"latin"` to `_should_enable_vlm_ocr()`. |
| 2.2 | Extend VLM OCR for Vietnamese | `mineru/backend/hybrid/hybrid_analyze.py` | If VLM supports it: change `language in ["ch", "en"]` to `language in ["ch", "en", "vi", "latin"]` in `_should_enable_vlm_ocr()` |

**Note**: The VLM may be trained primarily on Chinese/English. Enabling it for Vietnamese without verification could cause hallucinations. Test on sample Vietnamese PDFs before enabling.

---

### Phase 3: Vietnamese-Specific OCR (Optional — If Quality Is Poor)

| # | Task | File(s) | Change |
|---|------|---------|--------|
| 3.1 | Check PaddleOCR for dedicated Vietnamese model | PaddleOCR model zoo | PP-OCRv5 supports 106 languages. Check if there is a `vi` or `vie`-specific rec model and dict. |
| 3.2 | Add Vietnamese model config | `mineru/model/utils/pytorchocr/utils/resources/models_config.yml` | If a dedicated model exists, add: `vi: { det: ..., rec: ..., dict: ... }` |
| 3.3 | Skip latin mapping for vi | `mineru/model/ocr/pytorch_paddle.py` | If using dedicated model: remove `"vi"` from `latin_lang` so it uses its own config |

**Note**: PaddleOCR had [issues with Vietnamese diacritics](https://github.com/PaddlePaddle/PaddleOCR/issues/15189) (uppercase accented letters). A [PR added missing chars](https://github.com/PaddlePaddle/PaddleOCR/pull/15204). Verify MinerU's `ppocrv5_latin_dict.txt` includes Vietnamese characters (ă, â, ê, ô, ơ, ư, đ, etc.).

---

### Phase 4: Language Detection (Optional)

| # | Task | File(s) | Change |
|---|------|---------|--------|
| 4.1 | Verify fast-langdetect for Vietnamese | `mineru/utils/language.py` | `detect_lang()` uses fast-langdetect. Confirm it returns `"vi"` for Vietnamese text. |
| 4.2 | Add Vietnamese to post-processing if needed | `mineru/backend/vlm/vlm_middle_json_mkcontent.py`, `mineru/backend/pipeline/pipeline_middle_json_mkcontent.py` | Vietnamese uses spaces like Western text — current handling should be fine. Only change if you observe wrong spacing. |

---

## Recommended Order of Execution

1. **Phase 1** (Required): Add explicit `"vi"` support across CLI, Gradio, and FastAPI. Low risk, immediate UX improvement.
2. **Phase 2** (Optional): Investigate and optionally enable VLM OCR for Vietnamese.
3. **Phase 3** (Optional): Only if Phase 1 + latin model gives poor accuracy on Vietnamese diacritics.
4. **Phase 4** (Optional): Only if language detection or spacing issues appear.

---

## Testing Checklist

- [ ] CLI: `mineru -p vietnamese.pdf -o ./out -l vi` runs without error
- [ ] Gradio: Select "vi (Vietnamese)" and parse a Vietnamese PDF
- [ ] FastAPI: POST with `lang_list: ["vi"]` and verify response
- [ ] OCR quality: Test on Vietnamese PDF with diacritics (ă, â, ê, ô, ơ, ư, đ)
- [ ] Text PDF: Verify Vietnamese text extraction (non-OCR path) works
- [ ] Hybrid backend: Compare pipeline vs hybrid output quality for Vietnamese

---

## Files to Modify (Phase 1 Only)

| File | Line(s) | Edit |
|------|---------|------|
| `mineru/cli/client.py` | ~76 | Add `'vi'` to `click.Choice([...])` |
| `mineru/cli/gradio_app.py` | ~149-162 | Add `'vi (Vietnamese)'` to `other_lang` |
| `mineru/cli/fast_api.py` | ~134-151 | Add `- vi: Vietnamese` to description |
