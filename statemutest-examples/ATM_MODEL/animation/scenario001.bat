set modelsPath=..\..\..\statemutest-examples
set inputs=%modelsPath%\ATM_MODEL\animation\scenario001.inputs.txt
set instantiation=%modelsPath%\ATM_MODEL\animation\scenario001.instantiation.yaml
set xmiFilepath=%modelsPath%\ATM_MODEL\ATM_MODEL.uml
set libs=%modelsPath%\libs
set clazzpath=%libs%\statemutest-all-1.0.jar

java -cp %libs%\statemutest-all-1.0.jar statemutest.application.TestCaseAnimation -i %inputs% -s %instantiation% -u %xmiFilepath% -cp %clazzpath% -t atm.target.Atm