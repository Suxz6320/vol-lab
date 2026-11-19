"""同步设计稿到 Flutter App 的 assets/www 目录。"""
import os, shutil

SRC = r"c:\Users\33685\Desktop\val\volleylab"
DST = r"c:\Users\33685\Desktop\val\volleylab_app\assets\www"

pages_src = os.path.join(SRC, "pages")
for fname in os.listdir(pages_src):
    if fname.endswith(".html"):
        src = os.path.join(pages_src, fname)
        dst = os.path.join(DST, fname)
        content = open(src, encoding="utf-8").read()
        content = content.replace("../assets/", "assets/")
        content = content.replace("https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4.3.1/dist/index.global.js", "vendor/tailwind.js")
        content = content.replace("https://unpkg.com/lucide@1.8.0/dist/umd/lucide.min.js", "vendor/lucide.min.js")
        open(dst, "w", encoding="utf-8").write(content)
        print(f"  HTML: {fname}")

assets_src = os.path.join(SRC, "assets")
assets_dst = os.path.join(DST, "assets")
os.makedirs(assets_dst, exist_ok=True)
for fname in os.listdir(assets_src):
    shutil.copy2(os.path.join(assets_src, fname), os.path.join(assets_dst, fname))
    print(f"  Asset: {fname}")

print("\n同步完成。")
