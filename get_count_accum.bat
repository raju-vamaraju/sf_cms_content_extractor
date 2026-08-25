@echo off
setlocal EnableDelayedExpansion

set total=0

for /d %%d in ("C:\pyScripts\sf_cms_content_extractor\_media\*") do (
    for /f %%i in ('
        dir /a-d /b "%%d" ^| find /c /v ""
    ') do (
        echo %%~nxd : %%i files
        set /a total+=%%i
    )
)

echo.
echo ==========================
echo Grand Total : !total! files
echo ==========================