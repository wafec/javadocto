package statemutest.application;

import com.esotericsoftware.yamlbeans.YamlReader;
import com.esotericsoftware.yamlbeans.YamlWriter;
import com.github.javafaker.Faker;
import knowledge.modeling.Finder;
import org.apache.commons.cli.*;
import org.apache.log4j.Logger;
import org.w3c.dom.Element;
import statemutest.meter.*;
import statemutest.testcase.GenericGeoTestCaseGenerator;

import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;

public class TestMeter {
    static Logger log = Logger.getLogger(TestMeter.class);

    TestSetup setup;
    ArrayList<TestCaseObject> testCaseObjects;
    ArrayList<AbstractCoverage> coverages;

    String setupFilePath;
    ArrayList<String> testCasesFilePaths;

    TestMeter(String setupFilePath, ArrayList<String> testCasesFilePaths) {
        this.setupFilePath = setupFilePath;
        this.testCasesFilePaths = testCasesFilePaths;
        loadTestSetup();
        loadTestCaseObjects();
        loadCoverages();
    }

    final void loadTestSetup() {
        try {
            YamlReader reader = new YamlReader(new FileReader(setupFilePath));
            reader.getConfig().setClassTag("setup", TestSetup.class);
            reader.getConfig().setClassTag("meter", MeterSetup.class);
            reader.getConfig().setClassTag("stateInputMapping", GenericGeoTestCaseGenerator.UserDefinedStateInputMapping.class);
            reader.getConfig().setClassTag("conf", GenericSetup.class);
            setup =  reader.read(TestSetup.class);
        } catch (IOException exception) {
            log.error(exception);
        }
        if (setup == null)
            log.warn("Not possible to obtain test setup instance");
    }

    final void loadTestCaseObjects() {
        ArrayList<TestCaseObject> testCaseObjects = new ArrayList<>();
        for (String testCaseFilePath : testCasesFilePaths) {
            try {
                YamlReader reader = new YamlReader(new FileReader(testCaseFilePath));
                reader.getConfig().setClassTag("testcase", TestCaseObject.class);
                reader.getConfig().setClassTag("input", TestCaseObject.TestInput.class);
                reader.getConfig().setClassTag("expected", TestCaseObject.TestExpected.class);
                testCaseObjects.add(reader.read(TestCaseObject.class));
                log.info("Test file " + testCaseFilePath + " read");
            } catch (IOException exception) {
                log.warn("Test file " + testCaseFilePath + " not read");
                log.error(exception);
            }
        }
        this.testCaseObjects = testCaseObjects;
    }

    void generateMeasure() {
        CoverageMeter coverageMeter = new CoverageMeter(setup.generic, testCaseObjects, coverages);
        coverageMeter.measure();
        log.info("Measurement completed");
        MeasurementReport report = new MeasurementReport();
        Faker faker = new Faker();
        report.fictitiousName = faker.name().firstName();
        report.measures = coverages.stream().map(c -> c.obtainMeasure()).collect(Collectors.toList());
        try {
            String filename = "meter-report-" + report.fictitiousName + ".yaml";
            YamlWriter writer = new YamlWriter(new FileWriter(filename));
            writer.getConfig().setClassTag("report", MeasurementReport.class);
            writer.write(report);
            writer.close();
            log.info("Meter report saved as " + filename);
        } catch (IOException exception) {
            log.error(exception);
        }
    }

    final void loadCoverages() {
        coverages = new ArrayList<>();
        MeterSetup meterSetup = setup.getMethod(MeterSetup.class);
        for (String cov : meterSetup.coverages) {
            switch (cov) {
                case "transition":
                    TransitionCoverage transitionCoverage = new TransitionCoverage();
                    transitionCoverage.coverageTransitionSet = new ArrayList<>(setup.generic.getCoverageTransitionSetForTesting());
                    coverages.add(transitionCoverage);
                    break;
                case "pairwise":
                    PairwiseTransitionCoverage pairwiseTransitionCoverage = new PairwiseTransitionCoverage();
                    pairwiseTransitionCoverage.coverageTransitionIO = collectTransitionPairwiseSet();
                    coverages.add(pairwiseTransitionCoverage);
                    break;
                case "inopportune":
                    InopportuneTransitionCoverage inopportuneTransitionCoverage = new InopportuneTransitionCoverage();
                    inopportuneTransitionCoverage.coverageStateInputSet = collectStateInputSet();
                    coverages.add(inopportuneTransitionCoverage);
                    break;
                default:
                    log.warn("This code does not support the option " + cov);
            }
        }
    }

    ArrayList<PairBasedCoverage.Pair> collectTransitionPairwiseSet() {
        ArrayList<PairwiseTransitionCoverage.Pair> pairs = new ArrayList<>();
        Finder finder = Finder.newInstance(setup.generic.xmiFilePath);
        for (String transition : setup.generic.getCoverageTransitionSetForTesting()) {
            Element transitionXmi = finder.getElementByHash(transition);
            if (transitionXmi.hasAttribute("target")) {
                List<String> transitionsB = finder.getElements().stream().filter(e -> e.hasAttribute("source") && e.getTagName().equals("transition") &&
                    e.getAttribute("source").equals(transitionXmi.getAttribute("target"))).map(e -> e.getAttribute("xmi:id"))
                        .collect(Collectors.toList());
                if (transitionsB.size() > 0) {
                    pairs.addAll(new ArrayList<>(
                            transitionsB.stream().map(t -> {
                                PairwiseTransitionCoverage.Pair newPair = new PairwiseTransitionCoverage.Pair();
                                newPair.instanceA = transition;
                                newPair.instanceB = t;
                                return newPair;
                            }).collect(Collectors.toList())
                    ));
                }
            }
        }
        log.info(pairs.size() + " pairs for pairwise");
        return pairs;
    }

    ArrayList<PairBasedCoverage.Pair> collectStateInputSet() {
        ArrayList<PairBasedCoverage.Pair> pairs = new ArrayList<>();
        for (String state : setup.generic.getKnowableStateIdentitiesForTesting()) {
            for (String input : setup.generic.inputQualifiedNames) {
                PairBasedCoverage.Pair pair = new PairBasedCoverage.Pair();
                pair.instanceA = state;
                pair.instanceB = input;
                pairs.add(pair);
                // TO-DO: figure out which are the inputs mapped to states
                // these inputs are not considered as inopportune because they were modeled
            }
        }
        log.info(pairs.size() + " pairs for inopportune");
        return pairs;
    }

    public static void main(String[] args) {
        Options options = new Options();

        Option setupOption = new Option("s", "setup", true,"Test setup");
        setupOption.setRequired(true);
        options.addOption(setupOption);

        Option testCaseObjectsOption = new Option("t", "testcases", true, "Test cases");
        testCaseObjectsOption.setRequired(true);
        testCaseObjectsOption.setArgs(Option.UNLIMITED_VALUES);
        options.addOption(testCaseObjectsOption);

        CommandLineParser parser = new DefaultParser();
        try {
            CommandLine commandLine = parser.parse(options, args);
            new TestMeter(
                    commandLine.getOptionValue("setup"),
                    new ArrayList<>(Arrays.asList(commandLine.getOptionValues("testcases")))
            ).generateMeasure();
        } catch (ParseException exception) {
            log.error(exception);
        }
    }

    public static final class MeterSetup extends TestSetup.MethodSpecificSetup {
        public List<String> coverages;

        @Override
        public void fill(TestSetup.MethodSpecificSetup other) {
            if (!(other instanceof MeterSetup))
                return;
            ((MeterSetup) other).coverages = new ArrayList<>(coverages);
        }

        @Override
        public TestSetup.MethodSpecificSetup clone() {
            MeterSetup cloned = new MeterSetup();
            cloned.coverages = new ArrayList<>(coverages);
            return cloned;
        }
    }
}
