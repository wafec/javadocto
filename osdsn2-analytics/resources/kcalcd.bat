
@echo off
for /f "tokens=*" %%A in (%1) do (
    if exist out\matrix\%%A.7z (
        rmdir /Q /S out\matrix\tmp
        del extra.log
        mkdir out\matrix\tmp
        resources\7za.exe x out\matrix\%%A.7z -oout\matrix\tmp out\together\tmp\reduce\chosen
        mkdir out\matrix\tmp\source
        xcopy out\matrix\tmp\out\together\tmp\reduce\chosen\* out\matrix\tmp\source
        rmdir /Q /S out\matrix\tmp\out
        mkdir out\matrix\tmp\destination
        python osdsn2\documents\clustering.py out\matrix\tmp\source out\matrix\tmp\destination --extra extra.log
        resources\7za.exe d out\matrix\%%A.7z out\matrix
        copy extra.log out\matrix\tmp\extra.log
        resources\7za.exe a out\matrix\%%A.7z out\matrix\tmp
    )
)

rmdir /Q /S out\matrix\tmp