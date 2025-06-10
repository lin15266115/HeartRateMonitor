python -m nuitka ^
  --enable-plugin=pyqt5 ^
  --include-package=bleak ^
  --include-package=winrt ^
  --onefile --standalone ^
  --windows-console-mode=disable ^
  --output-dir=nuitka/v1.3.1 ^
  --remove-output ^
  --lto=no ^
  --jobs=6 ^
  __main__.py