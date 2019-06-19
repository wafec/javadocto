@echo off
for /f "tokens=*" %%A in (%1) do (
    if exist out\source\%%A.log (
        call :Foo %%A
    )
)
goto End

:Foo
set state=%1
if not exist out\together (
    mkdir out\together
)
if not exist out\together\%state% (
    mkdir out\together\%state%
)
python osdsn2\analytics\file_utils.py out\source %state%.log 2019
python osdsn2\analytics\parsers.py out\source %state%.log --parser full
python osdsn2\analytics\mining.py together out\objects\%state%.log out\together\%state%
rmdir /Q /S out\objects
goto :eof

:End