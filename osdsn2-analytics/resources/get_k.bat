
@echo off
for /f "tokens=*" %%A in (%1) do (
    if exist out\matrix\%%A.7z (
        rmdir /Q /S out\matrix\tmp
        mkdir out\matrix\tmp
        resources\7za.exe e out\matrix\%%A.7z -oout\matrix\tmp out\%%A.csv
        resources\7za.exe x out\matrix\%%A.7z -oout\matrix\tmp\source out\together\tmp\reduce\chosen
        resources\7za.exe x out\matrix\%%A.7z -oout\matrix\tmp\grouped out\together\tmp\reduce\grouped
        xcopy /S out\matrix\tmp\source\out\together\tmp\reduce\chosen\* out\matrix\tmp\source
        xcopy /S out\matrix\tmp\grouped\out\together\tmp\reduce\grouped\* out\matrix\tmp\grouped
        rmdir /Q /S out\matrix\tmp\grouped\out
        rmdir /Q /S out\matrix\tmp\source\out
        rmdir /Q /S out\matrix\tmp\source\results
        mkdir out\matrix\tmp\destination
        del kmeans.log
        python osdsn2\analytics\kmeans.py gk out\matrix\tmp\%%A.csv %2
        python osdsn2\analytics\kmeans.py process out\matrix\tmp\%%A.csv 10 out\matrix\tmp\source out\matrix\tmp\destination --better-choice kmeans.log %2
        resources\7za.exe d out\matrix\%%A.7z out\matrix
        copy kmeans.log out\matrix\tmp\matrix.log
        REM python osdsn2\analytics\kmeans.py check out\matrix\tmp\destination out\matrix\tmp\grouped
        resources\7za.exe a out\matrix\%%A.7z out\matrix\tmp
    )
)

rmdir /Q /S out\matrix\tmp