
@echo on

for /f "tokens=*" %%A in (%1) do (
    if exist out\%%A.7z (
        del out\%%A.7z
    )
)

call resources\flow.bat %1 %2

if not exist out\matrix (
    mkdir out\matrix
)
for /f "tokens=*" %%A in (%1) do (
    if exist out\%%A.7z (
        del out\matrix\%%A.7z
        copy out\%%A.7z out\matrix\%%A.7z
    )
)

call resources\kcalc.bat %1
