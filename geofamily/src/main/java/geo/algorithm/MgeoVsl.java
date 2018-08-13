package geo.algorithm;

import org.apache.commons.lang3.ArrayUtils;
import org.apache.log4j.Logger;

import java.util.Arrays;
import java.util.TimerTask;

public class MgeoVsl extends Mgeo {
    static Logger log = Logger.getLogger(MgeoVsl.class);

    BinaryInteger.Domain sizeDomain;

    public MgeoVsl(double tau, int numberOfIterations, int numberOfIndependentRuns, BinaryInteger.Domain sizeDomain,
            Objective[] objectives, BinaryInteger.Domain[] searchDomain) {
        super(tau, numberOfIterations, numberOfIndependentRuns,
                Arrays.asList(objectives).stream().map(o -> new ObjectiveWrapper(o)).toArray(Objective[]::new)
                , ArrayUtils.addAll(new BinaryInteger.Domain[] { sizeDomain }, searchDomain));
        this.sizeDomain = sizeDomain;
    }

    @Override
    protected TimerTask newMonitorInstance() {
        TimerTask monitor = new AbstractMonitor() {
            @Override
            public void run() {
                if (iterationCount > 0) {
                    progress = (((float) iterationCount) / numberOfIterations);
                    if (progress <= 1) {
                        log.info("Pareto has " + paretoFrontier.getElements().size() + " element(s), and test generation is " + (progress * 100) + "% completed (elapsed " + calculateElapsed() + ")");
                    }
                }
            }
        };
        return monitor;
    }

    @Override
    protected void chooseCandidateSolution() {
        super.chooseCandidateSolution();
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
            VslSequence vslSequence = new VslSequence(sequence);

            if (sequence.getTestSolution() != null) {
                Solution testSolution = sequence.getTestSolution();
                if (testSolution.getIndex() > vslSequence.getLength()) {
                    return Double.MAX_VALUE;
                }
            }

            return this.objective.eval(vslSequence.getData());
        }
    }

    public static class VslSequence {
        private Sequence sequence;

        public VslSequence(Sequence sequence) {
            this.sequence = sequence;
        }

        public Sequence getData() {
            return sequence.subSequence(1, getLength() + 1);
        }

        public int getLength() {
            return sequence.getProjectVariables()[0].getValue();
        }
    }
}
