@echo off
setlocal
if "%~1"=="" exit /b 2
if not exist "%~1" exit /b 2
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 3
pushd "%~1"
cl /nologo /std:c++17 /EHsc /W4 /O2 /Fe:selftest.exe /Fo:selftest.obj "%~dp0selftest_ctpi_online_core_v2.cpp"
if errorlevel 1 (popd & exit /b 4)
selftest.exe
set "CTPI_TEST_EXIT=%errorlevel%"
popd
exit /b %CTPI_TEST_EXIT%
