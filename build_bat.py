import os

def main(VER2):
    if os.path.exists("build.bat"):
        with open("build.bat", "r+", encoding="utf-8") as f:
            text = f.read()
            x = text.rfind("t")
            testnum = int(text[x+1:])+1
            f.seek(0)
            f.write(f"pyinstaller HRMLink.spec --clean --distpath=./_dist/{"v"+".".join(map(str, VER2))}-t{testnum}")
            f.truncate()
    if os.path.exists("version.txt"):
        with open("version.txt", "w", encoding="utf-8") as f:
            text_ = f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({", ".join(map(str, VER2))}),
    prodvers=({", ".join(map(str, VER2))}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '080404B0',
        [
          StringStruct('FileDescription', '通过低功耗蓝牙协议获取心率并显示 | Compiled using Pyinstaller'),
          StringStruct('ProductVersion', '{", ".join(map(str, VER2[0:3]))}'),
          StringStruct('LegalCopyright', 'Copyright (C) 2025 Zero_linofe | GPL-3.0 License'),
          StringStruct('CompanyName', 'Zero_linofe'),
          StringStruct('OriginalFilename', 'HRMLink.exe'),
        ])
    ]),
    VarFileInfo([VarStruct('Translation', [2052, 1200])])
  ]
)
"""
            f.write(text_)
    if os.path.exists("build2.bat"):
        with open("build2.bat", "w", encoding="utf-8") as f:
            text__ = rf"""chcp 65001 > nul

.\.conda\python -m nuitka ^
  --output-dir=_nuitka/v{".".join(map(str, VER2))} ^
  --output-filename=HRMLink.exe ^
  --enable-plugin=pyqt5 ^
  --include-package=bleak ^
  --include-package=winrt ^
  --onefile ^
  --standalone ^
  --windows-console-mode=disable ^
  --remove-output ^
  --lto=no ^
  --company-name="Zero_linofe" ^
  --product-name="HRMLink" ^
     --file-version={".".join(map(str, VER2))} ^
  --product-version={".".join(map(str, VER2))} ^
  --file-description="通过低功耗蓝牙协议获取心率并显示 | Compiled using Nuitka" ^
  --copyright="Copyright (C) 2025 Zero_linofe | GPL-3.0 License" ^
  __main__.py
"""
            f.write(text__)
    return None