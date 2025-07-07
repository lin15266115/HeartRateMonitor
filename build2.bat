chcp 65001 > nul

python -m nuitka ^
  --output-dir=_nuitka/v1.3.3.4 ^
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
  --file-version=1.3.3.4 ^
  --product-version=1.3.3.4 ^
  --file-description="通过低功耗蓝牙协议获取心率并显示 | Compiled using Nuitka" ^
  --copyright="Copyright (C) 2025 Zero_linofe | GPL-3.0 License" ^
  __main__.py