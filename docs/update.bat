del /q source\src.rst
sphinx-apidoc -f -o source ..
call make.bat html
start build\html\index.html