package statemutest.application;

import com.esotericsoftware.yamlbeans.YamlReader;
import com.esotericsoftware.yamlbeans.YamlWriter;
import com.github.javafaker.Faker;
import geo.algorithm.BinaryInteger;
import org.apache.commons.cli.*;
import org.apache.log4j.Logger;
import statemutest.modeling.JarGenerator;
import statemutest.testcase.GenericGeoTestCaseGenerator;
import statemutest.testcase.MgeoVslTestCaseGenerator;
import statemutest.testcase.TestCaseSet;
import statemutest.util.GenericHelper;
import xstate.support.Input;

import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;

public class TestCaseGeneration {
    static Logger log = Logger.getLogger(TestCaseGeneration.class);
    String testSetupFilePath;
    String destinationDirPath;
    GenericSetup genericSetup;
    File jarFile;
    File instanceSpecFile;

    ArrayList<String> generatedTestCaseFilePaths;

    TestCaseGeneration(String testSetupFilePath) {
        this(testSetupFilePath, null);
    }

    TestCaseGeneration(String testSetupFilePath, String destinationDirPath) {
        this.testSetupFilePath = testSetupFilePath;
        this.destinationDirPath = destinationDirPath;

        if (this.destinationDirPath == null) {
            this.destinationDirPath = ".";
        }
    }

    void generate() {
        try {
            TestCaseSet[] testCaseSets = null;
            YamlReader reader = getSetupReader();
            TestSetup setup = reader.read(TestSetup.class);
            if (setup == null) {
                log.error("Test setup is returning nil anyway, aborting");
                return;
            }
            
            if (setup.method instanceof MgeoVslSetup)
                testCaseSets = generateForMgeoVsl(setup);

            serializeTestCaseSets(testCaseSets);
            serializeSummary();
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

    YamlReader getSetupReader() throws IOException {
        YamlReader reader = new YamlReader(new FileReader(this.testSetupFilePath));
        reader.getConfig().setClassTag("setup", TestSetup.class);
        reader.getConfig().setClassTag("conf", GenericSetup.class);
        reader.getConfig().setClassTag("mgeovsl", MgeoVslSetup.class);
        reader.getConfig().setClassTag("stateInputMapping", GenericGeoTestCaseGenerator.UserDefinedStateInputMapping.class);
        return reader;
    }

    TestCaseSet[] generateForMgeoVsl(TestSetup setup) throws IOException {
        genericSetup = setup.generic;
        MgeoVslSetup methodSetup = setup.getMethod(MgeoVslSetup.class);
        generateForGeneric();
        MgeoVslTestCaseGenerator generator = new MgeoVslTestCaseGenerator(jarFile, genericSetup.testClassQualifiedName,
                instanceSpecFile,
                new ArrayList<String>(genericSetup.inputQualifiedNames),
                new ArrayList<String>(genericSetup.getStateIdentitiesForTesting()));
        if (setup.generic.userDefinedStateInputMappings != null)
            generator.setUserDefinedStateInputMappings(setup.generic.getUserDefinedStateInputMappingsForTesting()
                    .toArray(new GenericGeoTestCaseGenerator.UserDefinedStateInputMapping[setup.generic.userDefinedStateInputMappings.size()]));
        TestCaseSet[] testCaseSets = generator.generateTestDataSequence(methodSetup.tau, methodSetup.numberOfIterations,
                methodSetup.numberOfIndependentRuns,
                new BinaryInteger.Domain(methodSetup.minVars, methodSetup.maxVars),
                        new ArrayList<String>(genericSetup.getCoverageTransitionSetForTesting()));
        return testCaseSets;
    }

    void serializeTestCaseSets(TestCaseSet[] testCaseSets) {
        Faker faker = new Faker();
        generatedTestCaseFilePaths = new ArrayList<>();
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
                        testExpected.index = result.getIndex();
                        input.expectedSet.add(testExpected);
                    }
                }
            }
            testCaseObject.metadata = new HashMap<>();
            for (String key : testCaseSets[i].getMetadataKeys()) {
                String value = testCaseSets[i].getMetadataValue(key).toString();
                testCaseObject.metadata.put(key, value);
            }
            // a fictitious name is got before serialization
            testCaseObject.fictitiousName = faker.name().firstName();
            try {
                String fileName = "test-case-" + testCaseObject.fictitiousName + ".yaml";
                File file = new File(new File(destinationDirPath), fileName);
                YamlWriter writer = new YamlWriter(new FileWriter(file));
                writer.getConfig().setClassTag("testcase", TestCaseObject.class);
                writer.getConfig().setClassTag("input", TestCaseObject.TestInput.class);
                writer.getConfig().setClassTag("expected", TestCaseObject.TestExpected.class);
                writer.write(testCaseObject);
                writer.close();
                generatedTestCaseFilePaths.add(fileName);
                log.info("Test case generated as " + file.getPath());
            } catch (IOException exception) {
                log.error(exception.getMessage());
            }
        }
    }

    void serializeSummary() {
        TestSummary summary = new TestSummary();
        Faker faker = new Faker();
        summary.fictitiousName = faker.name().firstName();
        summary.statesIdentifier = genericSetup.stateIdentitiesIdentifier;
        summary.transitionsIdentifier = genericSetup.coverageTransitionSetIdentifier;
        summary.states = genericSetup.getStatesMapping();
        summary.transitions = genericSetup.getTransitionsMapping();
        summary.generatedTestCases = generatedTestCaseFilePaths;

        try {
            String filePath = "test-summary-" + summary.fictitiousName + ".yaml";
            File file = new File(new File(destinationDirPath), filePath);
            YamlWriter writer = new YamlWriter(new FileWriter(file));
            writer.getConfig().setClassTag("testSummary", TestSummary.class);
            writer.write(summary);
            writer.close();
            log.info("Summary generated as " + file.getPath());
        } catch (IOException exception) {
            log.error(exception.getMessage());
        }
    }

    public static void main(String... args) {
        Options options = new Options();

        // Test setup
        Option testSetupOption = new Option("s", "setup", true, "GenericSetup file path");
        testSetupOption.setRequired(true);
        options.addOption(testSetupOption);

        Option dirOption = new Option("d", "destination", true, "Set a directory as destination");
        dirOption.setRequired(false);
        options.addOption(dirOption);

        CommandLineParser parser = new DefaultParser();
        try {
            CommandLine line = parser.parse(options, args);
            new TestCaseGeneration(
                    line.getOptionValue("setup"),
                    line.hasOption("destination") ? line.getOptionValue("destination") : null
            ).generate();
        } catch (ParseException exception) {
            log.error(exception.getMessage());
        }
    }

    public final static class MgeoVslSetup extends TestSetup.MethodSpecificSetup {
        public double tau;
        public int numberOfIterations;
        public int numberOfIndependentRuns;
        public int maxVars;
        public int minVars;

        @Override
        public TestSetup.MethodSpecificSetup clone() {
            MgeoVslSetup cloned = new MgeoVslSetup();
            cloned.tau = tau;
            cloned.numberOfIterations = numberOfIterations;
            cloned.numberOfIndependentRuns = numberOfIndependentRuns;
            cloned.maxVars = maxVars;
            cloned.minVars = minVars;
            return cloned;
        }

        @Override
        public void fill(TestSetup.MethodSpecificSetup other) {
            if (!(other instanceof  MgeoVslSetup))
                return;
            if (other == null)
                return;
            MgeoVslSetup othergeo = (MgeoVslSetup) other;
            othergeo.tau = GenericHelper.copyIfNotNull(tau, othergeo.tau);
            othergeo.numberOfIterations = GenericHelper.copyIfNotNull(numberOfIterations, othergeo.numberOfIterations);
            othergeo.numberOfIndependentRuns = GenericHelper.copyIfNotNull(numberOfIndependentRuns, othergeo.numberOfIndependentRuns);
            othergeo.maxVars = GenericHelper.copyIfNotNull(maxVars, othergeo.maxVars);
            othergeo.minVars = GenericHelper.copyIfNotNull(minVars, othergeo.minVars);
        }
    }
}
