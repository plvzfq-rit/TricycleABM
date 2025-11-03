@echo off
set LOG_BASE=logs
if not exist %LOG_BASE% mkdir %LOG_BASE%

for /L %%i in (1,1,5) do (
    start /b py main.py --sim_count %%i > %LOG_BASE%\run_%%i_stdout.log 2>&1
)