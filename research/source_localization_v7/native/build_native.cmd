@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64
if errorlevel 1 exit /b %errorlevel%
cl /nologo /std:c++17 /O2 /fp:precise /EHsc /MD /LD native\native_query.cpp /Fonative\native_query.obj /Fenative\native_query.dll /link /IMPLIB:native\native_query.lib
exit /b %errorlevel%
