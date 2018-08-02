package statemutest.application.concretization;

import com.github.javafaker.Faker;
import org.apache.commons.text.WordUtils;
import org.apache.log4j.Logger;
import statemutest.application.TestCaseObject;

import java.util.ArrayList;

public class PythonConcretization extends GenericConcretization {
    static Logger log = Logger.getLogger(PythonConcretization.class);

    ArrayList<String> methodTemplates;

    public PythonConcretization(String testSummaryFilePath) {
        super(testSummaryFilePath);
    }

    @Override
    public TestScript generateTestScript() {
        methodTemplates = new ArrayList<>();
        String testName = testSummary.fictitiousName;
        StringBuilder writer = new StringBuilder();
        writer.append("class " + WordUtils.capitalize(testName) + "Test:\n");
        for (TestCaseObject test : testCaseObjects) {
            writer.append("    def test" + WordUtils.capitalize(test.fictitiousName) + "(self):\n");
            for (TestCaseObject.TestInput input : test.inputSet) {
                writer.append("        self.act_with_" + input.qualifiedName.replace(".", "_") +
                    "(");
                String methodTemplate = "act_with_" + input.qualifiedName.replace(".", "_") + "(self";
                ArrayList<String> paramList = new ArrayList<>(input.args.keySet());
                for (int i = 0; i < paramList.size(); i++) {
                    String param = paramList.get(i);
                    // we only support integers
                    String arg = input.args.get(param);
                    writer.append(param + "='" + arg + "'");
                    if (i + 1 < paramList.size())
                        writer.append(", ");
                    methodTemplate += ", " + param;
                }
                writer.append(")\n");
                methodTemplate += ")";
                if (!methodTemplates.contains(methodTemplate))
                    methodTemplates.add(methodTemplate);
                for (TestCaseObject.TestExpected expected : input.expectedSet) {
                    writer.append("        self.expect_for_" + expected.qualifiedName.replace(".", "_") +
                        "(");
                    methodTemplate = "expect_for_" + expected.qualifiedName.replace(".", "_") + "(self";
                    ArrayList<String> extrasList = new ArrayList<>(expected.extras.keySet());
                    for (int i = 0; i < extrasList.size(); i++) {
                        String extra = extrasList.get(i);
                        String arg = expected.extras.get(extra);
                        arg = testSummary.returnMatchedResultIfExists(arg);
                        writer.append(extra + "='" + arg + "'");
                        if (i + 1 < extrasList.size())
                            writer.append(", ");
                        methodTemplate += ", " + extra;
                    }
                    writer.append(")\n");
                    methodTemplate += ")";
                    if (!methodTemplates.contains(methodTemplate))
                        methodTemplates.add(methodTemplate);
                }
            }
            writer.append("\n");
        }
        for (final String methodTemplate : methodTemplates) {
            writer.append("    def " + methodTemplate + ":\n");
            writer.append("        # TO-DO\n");
            writer.append("        pass\n");
            writer.append("\n");
        }
        return new TestScript(testName, writer.toString());
    }
}
