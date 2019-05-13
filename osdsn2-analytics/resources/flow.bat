
set tester_include = --tester-include
set one_value = --one-value

@echo off
for /f "tokens=*" %%A in (%1) do (
    if exist out\source\%%A.log (
        if not exist out\%%A.7z (
            del kmeans.log
            @echo USE CASE: %%A > out\README
            @echo ALGORITHM: %2 >> out\README

            python osdsn2\analytics\file_utils.py out\source %%A.log 2019
            python osdsn2\analytics\parsers.py out\source %%A.log --parser full
            rmdir /Q /S out\together\tmp
            mkdir out\together\tmp
            python osdsn2\analytics\mining.py together out\objects\%%A.log out\together\tmp
            python osdsn2\analytics\mining.py results out\together\tmp %tester_include%
            python osdsn2\analytics\mining.py reduce out\together\tmp\results out\together\tmp\reduce
            python osdsn2\analytics\mining.py matrix out\together\tmp\reduce\chosen out\%%A.csv --algorithm %2 %one_value%
            resources\7za.exe a out\%%A.7z out\source\%%A.log out\together\tmp out\%%A.csv out\README
            del out\%%A.csv
            del out\README
            rmdir /Q /S out\objects\%%A.log
        )
    )
)

rmdir /Q /S out\together\tmp