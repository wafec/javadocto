package statemutest.testcase;

import geo.algorithm.BinaryInteger;
import geo.algorithm.MgeoVsl;
import geo.algorithm.Objective;

import java.io.File;
import java.util.ArrayList;

public class MgeoVslTestCaseGenerator extends TestCaseGenerator {
    public MgeoVslTestCaseGenerator(File jarFile, String testClass, File instanceSpecification, ArrayList<String> inputs,
                                    ArrayList<String> stateIdentities) {
        super(jarFile, testClass, instanceSpecification, inputs, stateIdentities);
    }

    public TestCaseSet[] generateTestDataSequence(double tau, int numberOfIterations, int numberOfIndependentRuns, BinaryInteger.Domain sizeDomain,
                                                ArrayList<String> coverageTransitionSet) {
        this.setupTestCaseGeneration(coverageTransitionSet);
        MgeoVsl mgeovsl = new MgeoVsl(tau, numberOfIterations, numberOfIndependentRuns, sizeDomain,
                new Objective[] { new TestObjectiveOne(), new TestObjectiveTwo() }, getSearchDomain(sizeDomain.getUpperBound()));
        mgeovsl.run();
        this.cleanUpTestCaseGeneration();
        return null;
    }

    class TestObjectiveOne implements Objective {
        public double eval(Object object) {
            return 0.0;
        }
    }

    class TestObjectiveTwo implements Objective {
        public double eval(Object object) {
            return 0.0;
        }
    }
}
