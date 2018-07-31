package statemutest.application;

import com.esotericsoftware.yamlbeans.YamlReader;
import com.esotericsoftware.yamlbeans.YamlWriter;
import geo.algorithm.BinaryInteger;
import org.apache.commons.cli.*;
import org.apache.log4j.BasicConfigurator;
import org.apache.log4j.Logger;
import statemutest.modeling.JarGenerator;
import statemutest.testcase.GenericGeoTestCaseGenerator;
import statemutest.testcase.MgeoVslTestCaseGenerator;
import statemutest.testcase.TestCaseSet;
import xstate.support.Input;

import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.stream.Collectors;

public class TestCaseGeneration {
    static Logger log = Logger.getLogger(TestCaseGeneration.class);
    String testCaseGeneratorName;
    String testSetupFilePath;
    GenericSetup genericSetup;
    File jarFile;
    File instanceSpecFile;

    TestCaseGeneration(String testCaseGeneratorName, String testSetupFilePath) {
        this.testCaseGeneratorName = testCaseGeneratorName;
        this.testSetupFilePath = testSetupFilePath;
    }

    void generate() {
        try {
            TestCaseSet[] testCaseSets = null;
            switch (testCaseGeneratorName) {
                case "mgeovsl":
                    testCaseSets = generateForMgeoVsl();
                    break;
            }
            serialize(testCaseSets);
            log.info("Test case generation terminates with success");
        } catch (IOException exception) {
            log.error(exception.getMessage());
        }
    }

    void generateForGeneric() {
        JarGenerator jarGenerator = new JarGenerator(genericSetup.classpath);
        jarFile = jarGenerator.generateJarFile(genericSetup.xmiFilePath);
        instanceSpecFile = new File(genericSetup.instanceSpecFilePath);
    }

    TestCaseSet[] generateForMgeoVsl() throws IOException {
        YamlReader reader = new YamlReader(new FileReader(this.testSetupFilePath));
        MgeoVslSetup setup = reader.read(MgeoVslSetup.class);
        genericSetup = setup.common;
        generateForGeneric();
        MgeoVslTestCaseGenerator generator = new MgeoVslTestCaseGenerator(jarFile, genericSetup.testClassQualifiedName,
                instanceSpecFile,
                new ArrayList<String>(genericSetup.inputQualifiedNames),
                new ArrayList<String>(genericSetup.getStateIdentitiesForTesting()));
        TestCaseSet[] testCaseSets = generator.generateTestDataSequence(setup.tau, setup.numberOfIterations,
                setup.numberOfIndependentRuns,
                new BinaryInteger.Domain(setup.minVars, setup.maxVars),
                        new ArrayList<String>(genericSetup.getCoverageTransitionSetForTesting()));
        return testCaseSets;
    }

    void serialize(TestCaseSet[] testCaseSets) {
        for (int i = 0; i < testCaseSets.length; i++) {
            TestCaseObject testCaseObject = new TestCaseObject();
            testCaseObject.inputSet = new ArrayList<>();
            for (int j = 0; j < testCaseSets[i].getInputDataSet().size(); j++) {
                Input inputdata = testCaseSets[i].getInputDataSet().get(j);
                Object object = testCaseSets[i].getObjectDataSet().get(j);
                TestCaseObject.TestInput input = new TestCaseObject.TestInput();
                input.qualifiedName = object.getClass().getCanonicalName();
                input.args = TestCaseObject.collectAttributeValuePairs(object);
                testCaseObject.inputSet.add(input);
                input.expectedSet = new ArrayList<>();
                if (inputdata instanceof GenericGeoTestCaseGenerator.Expected) {
                    GenericGeoTestCaseGenerator.Expected expected = (GenericGeoTestCaseGenerator.Expected) inputdata;
                    for (GenericGeoTestCaseGenerator.AbstractResult result : expected.getResults()) {
                        TestCaseObject.TestExpected testExpected = new TestCaseObject.TestExpected();
                        testExpected.qualifiedName = result.getClass().getCanonicalName();
                        testExpected.extras = TestCaseObject.collectAttributeValuePairs(result);
                        input.expectedSet.add(testExpected);
                    }
                }
            }
            testCaseObject.metadata = new HashMap<>();
            for (String key : testCaseSets[i].getMetadataKeys()) {
                String value = testCaseSets[i].getMetadataValue(key).toString();
                testCaseObject.metadata.put(key, value);
            }

            try {
                YamlWriter writer = new YamlWriter(new FileWriter("test-case-" + i + ".yaml"));
                writer.getConfig().setClassTag("testcase", TestCaseObject.class);
                writer.getConfig().setClassTag("input", TestCaseObject.TestInput.class);
                writer.getConfig().setClassTag("expected", TestCaseObject.TestExpected.class);
                writer.write(testCaseObject);
                writer.close();
            } catch (IOException exception) {
                log.error(exception.getMessage());
            }
        }
    }

    public static void main(String... args) {
        Options options = new Options();

        // Test case generator
        Option testCaseGeneratorOption = new Option("g", "generator", true, "Test case generator name");
        testCaseGeneratorOption.setRequired(true);
        options.addOption(testCaseGeneratorOption);

        // Test setup
        Option testSetupOption = new Option("s", "setup", true, "GenericSetup file path");
        testSetupOption.setRequired(true);
        options.addOption(testSetupOption);

        CommandLineParser parser = new DefaultParser();
        try {
            CommandLine line = parser.parse(options, args);
            new TestCaseGeneration(
                    line.getOptionValue("generator"),
                    line.getOptionValue("setup")
            ).generate();
        } catch (ParseException exception) {
            log.error(exception.getMessage());
        }
    }
}
