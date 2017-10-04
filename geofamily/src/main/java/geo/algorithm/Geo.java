package geo.algorithm;

import java.util.Arrays;
import java.util.Comparator;

public class Geo extends GenericGeo {
    public Geo(Objective objective, BinaryInteger.Domain[] domains) {
        super(new Objective[] { objective }, domains);
    }

    @Override
    protected void sortCandidatesSolutions() {
        final double bestRate = this.bestObjectivesRates[0];
        Arrays.sort(this.currentSolutions, (solution1, solution2) -> {
            double rate1 = solution1.getObjectiveRate(0) - bestRate;
            double rate2 = solution2.getObjectiveRate(0) - bestRate;
            return Double.compare(rate1, rate2);
        });
    }

    @Override
    protected void chooseCandidateSolution() {

    }
}
