# Hướng dẫn: Huấn luyện và tích hợp Model OCR tiếng Việt vào MinerU

## Tổng quan

MinerU dùng **PyTorchOCR** (chuyển từ PaddleOCR sang PyTorch). Để có model OCR tiếng Việt tốt, cần:

1. Huấn luyện model recognition tiếng Việt trong PaddleOCR
2. Export sang inference format
3. Chuyển sang PyTorch (.pth)
4. Thêm config và model vào MinerU

---

## Bước 1: Chuẩn bị môi trường

```bash
# Clone PaddleOCR
git clone https://github.com/PaddlePaddle/PaddleOCR.git
cd PaddleOCR

# Cài đặt (GPU)
pip install paddlepaddle-gpu
pip install -r requirements.txt
```

---

## Bước 2: Chuẩn bị Dataset

### Nguồn dữ liệu

| Nguồn | Số lượng | Link |
|-------|----------|------|
| VietOCR | ~441K ảnh | [pbcquoc/vietocr](https://github.com/pbcquoc/vietocr) |
| Nexdata Vietnamese OCR | 4,995 ảnh | [Nexdata-AI/4995-Vietnamese-OCR](https://github.com/Nexdata-AI/4995-Vietnamese-OCR-Images-Data-Images-with-Annotation-and-Transcription) |
| UIT-VNSC | 100K+ | [UIT-VNSC](https://github.com/nguyenvnbinh/UIT-VNSC) |

### Format PaddleOCR

Tạo file `rec_gt_train.txt` (tab-separated):

```
train_data/rec/train/word_001.jpg	Làm bước lần lượt
train_data/rec/train/word_002.jpg	những ý niệm ban đầu
```

**Cấu trúc thư mục:**
```
train_data/
  rec/
    rec_gt_train.txt
    rec_gt_val.txt
    train/
      word_001.jpg
      word_002.jpg
    val/
      ...
```

**Khuyến nghị:** Ít nhất 10,000–15,000 ảnh cho mô hình ổn định; 50,000+ cho chất lượng tốt.

---

## Bước 3: Tạo Dictionary tiếng Việt

Tạo file `ppocrv5_vi_dict.txt` với đầy đủ ký tự tiếng Việt:

```
0
1
2
...
9
A
B
...
a
b
...
ă
â
đ
ê
ô
ơ
ư
ạ
ả
ấ
ầ
ẩ
ẫ
ậ
ắ
ằ
ẳ
ẵ
ặ
ẹ
ẻ
ẽ
ế
ề
ể
ễ
ệ
ỉ
ị
ọ
ỏ
ố
ồ
ổ
ỗ
ộ
ớ
ờ
ở
ỡ
ợ
ụ
ủ
ứ
ừ
ử
ữ
ự
ỳ
ỵ
ỷ
ỹ
Ạ
Ả
...
```

Tham khảo: [PaddleOCR vi_dict.txt](https://github.com/PaddlePaddle/PaddleOCR/blob/main/ppocr/utils/dict/vi_dict.txt) và [PR #15204](https://github.com/PaddlePaddle/PaddleOCR/pull/15204) (thêm ký tự hoa).

---

## Bước 4: Chạy Training

### Tạo config `vi_PP-OCRv5_rec.yml`

Dựa trên `configs/rec/PP-OCRv5/latin_PP-OCRv5_rec.yml`:

```yaml
Global:
  character_dict_path: ppocr/utils/dict/ppocrv5_vi_dict.txt
  max_text_length: 25
  use_space_char: true

Train:
  dataset:
    name: SimpleDataSet
    data_dir: ./train_data/
    ext_op_transform_idx: 1
    label_file_list: ["train_data/rec/rec_gt_train.txt"]
  loader:
    shuffle: true
    batch_size_per_card: 256
    drop_last: true
    num_workers: 4

Eval:
  dataset:
    name: SimpleDataSet
    data_dir: ./train_data/
    label_file_list: ["train_data/rec/rec_gt_val.txt"]
  loader:
    shuffle: false
    batch_size_per_card: 256
    drop_last: false
```

### Chạy training

```bash
# Fine-tune từ latin model (khuyến nghị)
python tools/train.py -c configs/rec/PP-OCRv5/latin_PP-OCRv5_rec.yml \
  -o Global.pretrained_model=./pretrain_models/latin_PP-OCRv5_rec_train/best_accuracy \
  Global.character_dict_path=ppocr/utils/dict/ppocrv5_vi_dict.txt \
  Train.dataset.label_file_list=["train_data/rec/rec_gt_train.txt"] \
  Eval.dataset.label_file_list=["train_data/rec/rec_gt_val.txt"]
```

---

## Bước 5: Export sang Inference Format

```bash
python tools/export_model.py \
  -c configs/rec/PP-OCRv5/vi_PP-OCRv5_rec.yml \
  -o Global.pretrained_model=./output/vi_rec/best_accuracy \
  Global.save_inference_dir=./inference/vi_rec/
```

Kết quả: `inference/vi_rec/inference.pdmodel`, `inference.pdiparams`

---

## Bước 6: Chuyển sang PyTorch (.pth)

MinerU dùng **PaddleOCR2Pytorch**. Có thể:

### Cách A: Dùng PaddleOCR2Pytorch

```bash
git clone https://github.com/frotms/PaddleOCR2Pytorch.git
cd PaddleOCR2Pytorch

# Chuyển model (cần script convert - xem repo)
python convert.py --input inference/vi_rec --output vi_PP-OCRv5_rec_infer.pth
```

### Cách B: Kiểm tra cấu trúc model hiện có

MinerU lấy model từ `opendatalab/PDF-Extract-Kit-1.0`. Tải model latin về:

```bash
# Xem cấu trúc model hiện có
ls ~/.cache/huggingface/hub/models--opendatalab--PDF-Extract-Kit-1.0/snapshots/*/models/OCR/paddleocr_torch/
```

Model cần có format tương thích với `TextRecognizer` trong MinerU (SVTR + CTCHead).

---

## Bước 7: Tích hợp vào MinerU

### 7.1 Thêm config vào `models_config.yml`

```yaml
  vi:
    det: ch_PP-OCRv5_det_infer.pth
    rec: vi_PP-OCRv5_rec_infer.pth
    dict: ppocrv5_vi_dict.txt
```

### 7.2 Thêm arch config cho model vi

Trong `mineru/model/utils/pytorchocr/utils/resources/arch_config.yaml`, thêm (thay `XXX` = số ký tự trong dict + 1):

```yaml
vi_PP-OCRv5_rec_infer:
  model_type: rec
  algorithm: SVTR_HGNet
  Transform:
  Backbone:
    name: PPLCNetV3
    scale: 0.95
  Head:
    name: MultiHead
    out_channels_list:
      CTCLabelDecode: XXX   # = len(ppocrv5_vi_dict.txt) + 1 (blank)
    head_list:
      - CTCHead:
          Neck:
            name: svtr
            dims: 120
            depth: 2
            hidden_dims: 120
            kernel_size: [ 1, 3 ]
            use_guide: True
          Head:
            fc_decay: 0.00001
      - NRTRHead:
          nrtr_dim: 384
          max_text_length: 25
```

### 7.3 Bỏ mapping "vi" -> "latin" trong `pytorch_paddle.py`

```python
# Thêm điều kiện: vi dùng config riêng, không map sang latin
if self.lang == 'vi':
    pass  # giữ nguyên 'vi'
elif self.lang in latin_lang:
    self.lang = 'latin'
```

### 7.4 Đặt model

**Option 1 – Local:** Đặt `vi_PP-OCRv5_rec_infer.pth` vào thư mục models:

```
~/.cache/mineru/models/OCR/paddleocr_torch/vi_PP-OCRv5_rec_infer.pth
```

**Option 2 – HuggingFace:** Đẩy model lên repo và cập nhật `allow_patterns` trong `models_download_utils.py` để tải model `vi`.

**Option 3 – Config local:** Dùng `mineru.template.json`:

```json
{
  "models-dir": {
    "pipeline": "/path/to/pipeline/models"
  }
}
```

Đặt `vi_PP-OCRv5_rec_infer.pth` trong `pipeline/models/OCR/paddleocr_torch/`.

---

## Bước 8: Kiểm tra

```bash
mineru -p vietnamese_scan.pdf -o ./out -l vi -b pipeline
```

---

## Tài liệu tham khảo

- [PaddleOCR Text Recognition Training](https://paddleocr.ai/main/en/ppocr/model_train/recognition.html)
- [Hướng dẫn fine-tune PaddleOCR (tiếng Việt)](https://thigiacmaytinh.com/huong-dan-fine-turning-mo-hinh-paddleocr-recognition-voi-custom-dataset/)
- [OCRVietnamese - NMThanh123](https://github.com/NMThanh123/OCRVietnamese)
- [PaddleOCR2Pytorch](https://github.com/frotms/PaddleOCR2Pytorch)
- [VietOCR](https://github.com/pbcquoc/vietocr)

---

## Checklist tích hợp

- [ ] Train model trong PaddleOCR
- [ ] Export inference (.pdmodel, .pdiparams)
- [ ] Convert sang PyTorch (.pth)
- [ ] Tạo `ppocrv5_vi_dict.txt` đầy đủ ký tự
- [ ] Thêm `vi` vào `models_config.yml`
- [ ] Thêm `vi_PP-OCRv5_rec_infer` vào `arch_config.yaml` (đúng output dim)
- [ ] Sửa `pytorch_paddle.py`: vi không map sang latin
- [ ] Đặt file model vào đúng thư mục
- [ ] Test: `mineru -p test.pdf -o out -l vi -b pipeline`

---

## Lưu ý

- **GPU:** Training nên dùng GPU (16GB+ VRAM cho batch lớn).
- **Thời gian:** 10K ảnh ~ vài giờ; 50K+ có thể ~ 1 ngày.
- **PaddleOCR2Pytorch:** Cần tương thích với `latin_PP-OCRv5_rec` (SVTR + CTCHead). Nếu PaddleOCR2Pytorch chưa hỗ trợ PP-OCRv5, có thể cần tự viết script convert.
