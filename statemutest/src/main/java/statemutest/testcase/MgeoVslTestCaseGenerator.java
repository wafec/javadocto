package statemutest.testcase;

import geo.algorithm.*;
import org.apache.log4j.Logger;
import xstate.support.Input;

import java.io.File;
import java.util.ArrayList;
import java.util.List;

public class MgeoVslTestCaseGenerator extends GenericGeoTestCaseGenerator {
    static Logger log = Logger.getLogger(MgeoVslTestCaseGenerator.class);

    public MgeoVslTestCaseGenerator(File jarFile, String testClass, File instanceSpecification, ArrayList<String> inputs,
                                    ArrayList<String> stateIdentities) {
        super(jarFile, testClass, instanceSpecification, inputs, stateIdentities);
    }

    public TestCaseSet[] generateTestDataSequence(double tau, int numberOfIterations, int numberOfIndependentRuns, BinaryInteger.Domain sizeDomain,
                                                  ArrayList<String> coverageTransitionSet) {
        log.info("Test data sequence generation process started");
        this.setupTestCaseGeneration(coverageTransitionSet);
        int sizeBeforeEventsOffset = calculateSizeBeforeEventsOffset();
        int lower, upper;
        lower = sizeDomain.getLowerBound() + sizeBeforeEventsOffset + 1;
        upper = sizeDomain.getUpperBound() + sizeBeforeEventsOffset + 1;
        sizeDomain = new BinaryInteger.Domain(lower, upper);
        MgeoVsl mgeovsl = new MgeoVsl(tau, numberOfIterations, numberOfIndependentRuns, sizeDomain,
                new Objective[] { new GenericTestObjective(), new TestObjectiveTwo() }, getSearchDomain(sizeDomain.getUpperBound() - sizeBeforeEventsOffset));
        mgeovsl.run();
        ParetoFrontier paretoFrontier = mgeovsl.getParetoFrontier();
        List<ParetoFrontier.Element> frontierElements = paretoFrontier.getElements();
        TestCaseSet[] testCaseSets = new TestCaseSet[frontierElements.size()];
        int i = 0;
        for (ParetoFrontier.Element element : frontierElements) {
            ArrayList<Input> inputDataSet = evaluateTestClassInstance(new MgeoVsl.VslSequence(element.getSequence()).getData());
            ArrayList<Object> objectDataSet = generateObjectDataSet(inputDataSet);
            TestCaseSet testCaseSet = new TestCaseSet(inputDataSet, objectDataSet);
            testCaseSet.putMetadata("iteration", element.getIterationIndex());
            for (int j = 0; j < element.getObjectivesRates().length; j++) {
                testCaseSet.putMetadata("objective_rate_" + (j + 1), element.getObjectivesRates()[j]);
            }
            testCaseSets[i] = testCaseSet;
            i++;
        }
        // without this there is not possible to get right inputs
        this.cleanUpTestCaseGeneration();
        log.info("Test data sequence generation process completed");
        return testCaseSets;
    }

    class TestObjectiveTwo implements Objective {
        public double eval(Object object) {
            Sequence sequence = (Sequence) object;
            int length = sequence.getProjectVariables().length;
            return length;
        }
    }
}
