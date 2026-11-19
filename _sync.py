import os, shutil

SRC = r"c:\Users\33685\Desktop\val\volleylab"
DST = r"c:\Users\33685\Desktop\val\volleylab_app\assets\www"

# HTML
pages_src = os.path.join(SRC, "pages")
for fname in os.listdir(pages_src):
    if fname.endswith(".html"):
        content = open(os.path.join(pages_src, fname), encoding="utf-8").read()
        content = content.replace("../assets/", "assets/")
        content = content.replace("../models/", "models/")
        open(os.path.join(DST, fname), "w", encoding="utf-8").write(content)

# Assets
for sub in ["assets", "models", "vendor"]:
    src = os.path.join(SRC, sub)
    dst = os.path.join(DST, sub)
    os.makedirs(dst, exist_ok=True)
    if os.path.isdir(src):
        for f in os.listdir(src):
            sp = os.path.join(src, f)
            dp = os.path.join(dst, f)
            if os.path.isfile(sp):
                shutil.copy2(sp, dp)

print("Sync done!")
