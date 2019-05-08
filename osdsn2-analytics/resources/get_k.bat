
@echo off
for /f "tokens=*" %%A in (%1) do (
    if exist out\matrix\%%A.7z (
        rmdir /Q /S out\matrix\tmp
        mkdir out\matrix\tmp
        resources\7za.exe e out\matrix\%%A.7z -oout\matrix\tmp out\%%A_minhash.csv
        resources\7za.exe e out\matrix\%%A.7z -oout\matrix\tmp\source out out\together\tmp
        rmdir /Q /S out\matrix\tmp\source\results
        mkdir out\matrix\tmp\destination
        python osdsn2\analytics\kmeans.py kmeans out\matrix\tmp\%%A_minhash.csv
        python osdsn2\analytics\kmeans.py konly out\matrix\tmp\%%A_minhash.csv 10 out\matrix\tmp\source out\matrix\tmp\destination --better-choice kmeans.log
        resources\7za.exe a out\matrix\%%A.konly.7z out\matrix\tmp
    )
)

rmdir /Q /S out\matrix\tmp