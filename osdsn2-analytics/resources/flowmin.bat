
@echo off
for /f "tokens=*" %%A in (%1) do (
    if exist out\source\%%A.log (
        if not exist out\%%A.7z (
            del kmeans.log
            del extra.log
            @echo USE CASE: %%A > out\README
            @echo ALGORITHM: %2 >> out\README
            @echo > extra.log

            python osdsn2\analytics\file_utils.py out\source %%A.log 2019 --extra-log extra.log
            python osdsn2\analytics\parsers.py out\source %%A.log --parser full --extra-log extra.log
            rmdir /Q /S out\together\tmp
            mkdir out\together\tmp
            python osdsn2\analytics\mining.py --extra-log extra.log together out\objects\%%A.log out\together\tmp
            python osdsn2\analytics\mining.py --extra-log extra.log results out\together\tmp
            python osdsn2\analytics\mining.py --extra-log extra.log reduce out\together\tmp\results out\together\tmp\reduce
            resources\7za.exe a out\%%A.7z out\source\%%A.log out\together\tmp out\%%A.csv out\README extra.log out\objects
            del out\%%A.csv
            del out\README
            del extra.log
            rmdir /Q /S out\objects\%%A.log
        )
    )
)

rmdir /Q /S out\together\tmp