package statemutest.application.concretization;

import com.esotericsoftware.yamlbeans.YamlReader;
import org.apache.log4j.Logger;
import statemutest.application.TestCaseObject;
import statemutest.application.TestSummary;

import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;

public abstract class GenericConcretization {
    static Logger log = Logger.getLogger(GenericConcretization.class);

    String testSummaryFilePath;
    TestSummary testSummary;
    ArrayList<TestCaseObject> testCaseObjects;

    protected GenericConcretization(String testSummaryFilePath) {
        this.testSummaryFilePath = testSummaryFilePath;
        this.loadFiles();
    }

    final void loadFiles() {
        try {
            YamlReader reader = new YamlReader(new FileReader(testSummaryFilePath));
            reader.getConfig().setClassTag("testSummary", TestSummary.class);
            testSummary = reader.read(TestSummary.class);
            log.debug("Test summary in " + testSummaryFilePath + " is read");
        } catch (IOException exception) {
            log.error(exception.getMessage());
        }

        testCaseObjects = new ArrayList<>();
        for (final String testCaseFilePath : testSummary.generatedTestCases) {
            try {
                YamlReader reader = new YamlReader(new FileReader(testCaseFilePath));
                reader.getConfig().setClassTag("testcase", TestCaseObject.class);
                reader.getConfig().setClassTag("input", TestCaseObject.TestInput.class);
                reader.getConfig().setClassTag("expected", TestCaseObject.TestExpected.class);
                testCaseObjects.add(reader.read(TestCaseObject.class));
                log.debug("Test object in " + testCaseFilePath + " is read");
            } catch (IOException exception) {
                log.error(exception.getMessage());
            }
        }
    }

    public abstract TestScript generateTestScript();

    public static class TestScript {
        public String testScriptFictitiousName;
        public String testScriptBody;

        public TestScript() {

        }

        public TestScript(String testScriptFictitiousName, String testScriptBody) {
            this.testScriptFictitiousName = testScriptFictitiousName;
            this.testScriptBody = testScriptBody;
        }
    }
}
