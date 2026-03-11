# %% [markdown]
# # MinerU trên Google Colab - Hỗ trợ tiếng Việt
# 
# Script chạy MinerU (fork với hỗ trợ tiếng Việt) trên Google Colab.
# 
# **Mở trong Colab:** [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/spkzr/MinerU/blob/master/mineru_colab.py)
# 
# **Fork:** https://github.com/spkzr/MinerU

# %% [markdown]
# ## 1. Cài đặt môi trường

# %%
# Chạy cell này trước - Cài đặt MinerU từ fork có hỗ trợ tiếng Việt
!pip install -q uv
# Cài từ fork có hỗ trợ tiếng Việt (có thể mất 3-5 phút)
!uv pip install -q "git+https://github.com/spkzr/MinerU.git#egg=mineru[all]"

# %%
# Kiểm tra cài đặt
!mineru --version

# %% [markdown]
# ## 2. Upload PDF và chạy OCR

# %%
# Tạo thư mục input/output
!mkdir -p /content/input /content/output

# %%
# CÁCH 1: Upload file PDF qua giao diện Colab
# Chạy cell này và bấm "Choose Files" để upload PDF
from google.colab import files
uploaded = files.upload()

# Di chuyển file vào thư mục input
import shutil
for filename in uploaded.keys():
    shutil.move(filename, f"/content/input/{filename}")
    print(f"Đã upload: {filename}")

# %%
# CÁCH 2: Tải PDF từ URL
# Bỏ comment và thay URL nếu muốn tải PDF từ link
# !wget -P /content/input "https://example.com/your-file.pdf"

# %% [markdown]
# ## 3. Chạy MinerU với tiếng Việt

# %%
# Chạy OCR - Thay tên file PDF của bạn
PDF_FILE = "/content/input/your_file.pdf"  # <-- SỬA TÊN FILE Ở ĐÂY

# Liệt kê file trong input để chọn
import os
input_files = [f for f in os.listdir("/content/input") if f.endswith(".pdf")]
print("Các file PDF có sẵn:", input_files)
if input_files:
    PDF_FILE = f"/content/input/{input_files[0]}"
    print(f"Sử dụng file: {PDF_FILE}")

# %%
# Chạy MinerU với ngôn ngữ tiếng Việt (vi) và backend pipeline
# Pipeline chạy được trên CPU, phù hợp Colab free tier
import subprocess
result = subprocess.run(
    ["mineru", "-p", PDF_FILE, "-o", "/content/output", "-l", "vi", "-b", "pipeline"],
    capture_output=False
)
print("Hoàn thành!" if result.returncode == 0 else f"Lỗi: {result.returncode}")

# %%
# Nếu có GPU và muốn dùng hybrid (chính xác hơn nhưng cần nhiều RAM):
# subprocess.run(["mineru", "-p", PDF_FILE, "-o", "/content/output", "-l", "vi", "-b", "hybrid-auto-engine"])

# %% [markdown]
# ## 4. Xem kết quả

# %%
# Liệt kê file output
!ls -la /content/output/

# %%
# Tìm file Markdown đã extract
import glob
md_files = glob.glob("/content/output/**/*.md", recursive=True)
print("Các file Markdown:", md_files)

# %%
# Xem nội dung file Markdown đầu tiên
if md_files:
    with open(md_files[0], "r", encoding="utf-8") as f:
        content = f.read()
    print(content[:3000])  # In 3000 ký tự đầu
else:
    print("Chưa tìm thấy file .md. Kiểm tra thư mục output.")

# %%
# Tải file kết quả về máy
if md_files:
    from google.colab import files
    files.download(md_files[0])
    print("Đã tải file về máy!")

# %%
# Tải toàn bộ thư mục output dưới dạng zip
import os
import subprocess
if os.path.exists("/content/output"):
    subprocess.run(["zip", "-r", "/content/output.zip", "output"], cwd="/content")
    if os.path.exists("/content/output.zip"):
        from google.colab import files
        files.download("/content/output.zip")
        print("Đã tải output.zip!")
