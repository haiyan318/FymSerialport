@echo off
REM 在 docgui 虚拟环境中启动上位机（不新建/不切换其它环境）
set PY=D:\apps\anaconda3\envs\docgui\python.exe
"%PY%" "%~dp0fym_serialport.py"
