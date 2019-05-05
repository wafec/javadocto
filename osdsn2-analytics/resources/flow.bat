
@echo off
for /f "tokens=*" %%A in (%1) do (
    python osdsn2\analytics\file_utils.py out\source %%A.log 2019
    python osdsn2\analytics\parsers.py out\source %%A.log --parser full
    rmdir /Q /S out\together\tmp
    mkdir out\together\tmp
    python osdsn2\analytics\mining.py together out\objects\%%A.log out\together\tmp
    python osdsn2\analytics\mining.py results out\together\tmp
    python osdsn2\analytics\mining.py matrix out\together\tmp\results out\%%A_minhash.csv
    resources\7za.exe a out\%%A.7z out\source\%%A.log out\together\tmp out\%%A_minhash.csv
    rm out\%%A_minhash.csv
    rmdir /Q /S out\objects\%%A.log
)

rmdir /Q /S out\together\tmp