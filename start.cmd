@echo off
rem Windows launcher for start.sh: run "start" or ".\start.cmd" from PowerShell or cmd.
rem It runs start.sh with Git Bash in this same window. The "bash" on PATH is often
rem WSL's Linux bash, which cannot run the Windows virtualenv, so it is not used.
setlocal

set "GIT_BASH="
for /f "delims=" %%G in ('where git 2^>nul') do (
  if not defined GIT_BASH if exist "%%~dpG..\bin\bash.exe" set "GIT_BASH=%%~dpG..\bin\bash.exe"
)
if not defined GIT_BASH if exist "%ProgramFiles%\Git\bin\bash.exe" set "GIT_BASH=%ProgramFiles%\Git\bin\bash.exe"
if not defined GIT_BASH (
  echo Git for Windows is required to run start.sh: https://git-scm.com/download/win
  exit /b 1
)

pushd "%~dp0"
"%GIT_BASH%" ./start.sh %*
set "EXIT_CODE=%ERRORLEVEL%"
popd
exit /b %EXIT_CODE%
