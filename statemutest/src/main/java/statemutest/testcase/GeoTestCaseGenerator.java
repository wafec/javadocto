package statemutest.testcase;

import com.google.common.collect.Sets;
import geo.algorithm.Geo;
import geo.algorithm.Objective;
import geo.algorithm.Sequence;
import org.apache.log4j.Logger;
import xstate.support.Input;

import java.io.File;
import java.util.ArrayList;

public class GeoTestCaseGenerator extends TestCaseGenerator {
    static final Logger log = Logger.getLogger(GeoTestCaseGenerator.class);
    Geo geo;

    public GeoTestCaseGenerator(File jarFile, String testClass, File instanceSpecification,
                                ArrayList<String> inputs, ArrayList<String> stateIdentities) {
        super(jarFile, testClass, instanceSpecification, inputs, stateIdentities);
    }

    public TestCaseSet generateTestDataSequence(double tau, int numberOfIterations, ArrayList<String> coverageTransitionSet, int maxEvents) {
        log.info("Test data sequence generation process started");
        this.setupTestCaseGeneration(coverageTransitionSet);
        geo = new Geo(tau, numberOfIterations, new TestObjective(), getSearchDomain(maxEvents));
        geo.run();
        this.cleanUpTestCaseGeneration();
        Sequence sequence = geo.getBestSequence();
        ArrayList<Input> inputDataSet = evaluateTestClassInstance(sequence);
        ArrayList objectDataSet = generateObjectDataSet(inputDataSet);
        log.info("Test data sequence generation process completed");
        TestCaseSet testCaseSet = new TestCaseSet(inputDataSet, objectDataSet);
        testCaseSet.putMetadata("best_iteration", geo.getBestIteration());
        testCaseSet.putMetadata("best_objective_rate", geo.getBestObjectiveRate());
        return testCaseSet;
    }

    class TestObjective implements Objective {
        @Override
        public double eval(Object object) {
            Sequence sequence = (Sequence) object;
            evaluateTestClassInstance(sequence);
            Sets.SetView<String> setView = Sets.difference(coverageTransitionHashSet, exercisedTransitionSet);
            double value = setView.size();
            if (value > 0) {
                double branchScale = 1000000.0;
                double normalizedBranchDistance = currentBranchDistance / branchScale;
                value += normalizedBranchDistance;
            }
            return value;
        }
    }
}
