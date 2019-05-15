
@echo off
for /f "tokens=*" %%A in (%1) do (
    if exist out\matrix\%%A.7z (
        rmdir /Q /S out\matrix\tmp
        mkdir out\matrix\tmp
        resources\7za.exe e out\matrix\%%A.7z -oout\matrix\tmp out\%%A.csv
        resources\7za.exe x out\matrix\%%A.7z -oout\matrix\tmp\source out\together\tmp\reduce\chosen
        resources\7za.exe x out\matrix\%%A.7z -oout\matrix\tmp\grouped out\together\tmp\reduce\grouped
        xcopy out\matrix\tmp\source\out\together\tmp\reduce\chosen\* out\matrix\tmp\source
        rmdir /Q /S out\matrix\tmp\source\out\together\tmp\reduce\chosen
        xcopy out\matrix\tmp\grouped\out\together\tmp\reduce\grouped\* out\matrix\tmp\grouped
        rmdir /Q /S out\matrix\tmp\grouped\out\together\tmp\reduce\grouped
        rmdir /Q /S out\matrix\tmp\source\results
        mkdir out\matrix\tmp\destination
        del kmeans.log
        python osdsn2\analytics\kmeans.py kmeans out\matrix\tmp\%%A.csv
        python osdsn2\analytics\kmeans.py konly out\matrix\tmp\%%A.csv 10 out\matrix\tmp\source out\matrix\tmp\destination --better-choice kmeans.log
        resources\7za.exe d out\matrix\%%A.7z out\matrix
        copy kmeans.log out\matrix\tmp\matrix.log
        python osdsn2\analytics\kmeans.py check out\matrix\tmp\destination out\matrix\tmp\grouped
        resources\7za.exe a out\matrix\%%A.7z out\matrix\tmp
    )
)

rmdir /Q /S out\matrix\tmp