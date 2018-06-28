package geo.algorithm;

import org.apache.commons.lang3.ArrayUtils;

import java.util.Arrays;

public class MgeoVsl extends Mgeo {
    BinaryInteger.Domain sizeDomain;

    public MgeoVsl(double tau, int numberOfIterations, int numberOfIndependentRuns, BinaryInteger.Domain sizeDomain,
            Objective[] objectives,
                   BinaryInteger.Domain[] searchDomain) {
        super(tau, numberOfIterations, numberOfIndependentRuns,
                Arrays.asList(objectives).stream().map(o -> new ObjectiveWrapper(o)).toArray(Objective[]::new)
                , ArrayUtils.addAll(new BinaryInteger.Domain[] { sizeDomain }, searchDomain));
        this.sizeDomain = sizeDomain;
    }

    static class ObjectiveWrapper implements Objective {
        Objective objective;

        public ObjectiveWrapper(Objective objective) {
            this.objective = objective;
        }

        public double eval(Object object) {
            // assuming that object is a sequence
            // to be faster I am not adding extra ifs
            Sequence sequence = (Sequence) object;
            int length = sequence.getProjectVariables()[0].getValue();
            return this.objective.eval(sequence.subSequence(1, length + 1));
        }
    }
}
