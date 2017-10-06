package geo.algorithm;

import java.util.Arrays;
import java.util.Comparator;

public class Geo extends GenericGeo {
    protected Sequence bestSequence;
    protected int numberOfIterations;
    protected int iterationCount;
    protected int bestIteration;

    public Geo(double tau, int numberOfIterations, Objective objective, BinaryInteger.Domain[] searchDomain) {
        super(tau, new Objective[] { objective }, searchDomain);
        this.numberOfIterations = numberOfIterations;
    }

    @Override
    protected void initialization() {
        super.initialization();
        this.bestSequence = this.currentSequence;
        this.iterationCount = 0;
        this.bestIteration = 0;
    }

    @Override
    protected void sortCandidatesSolutions() {
        final double bestRate = this.bestObjectivesRates[0];
        Arrays.sort(this.currentSolutions, (solution1, solution2) -> {
            double rate1 = solution1.getObjectiveRate(0) - bestRate;
            double rate2 = solution2.getObjectiveRate(0) - bestRate;
            return Double.compare(rate1, rate2);
        });
        for (int i = 0; i < this.currentSolutions.length; i++) {
            this.currentSolutions[i].setK(i + 1);
        }
        Arrays.sort(this.currentSolutions, Comparator.comparingInt(Solution::getSolutionIndex));
    }

    @Override
    protected void chooseCandidateSolution() {
        double n;
        int i;
        double c;
        int k;
        do {
            i = this.randomGenerator.nextInt(this.currentSolutions.length);
            n = this.randomGenerator.nextDouble();
            k = this.currentSolutions[i].getK();
            c = Math.pow(k, -this.tau);
        } while(n > c);

        this.currentSequence.applySolution(this.currentSolutions[i]);
        this.calculateCurrentObjectivesRates();
    }

    @Override
    protected void update() {
        double objectiveRate = this.objectives[0].eval(this.currentSequence);
        if (objectiveRate < this.bestObjectivesRates[0]) {
            this.bestObjectivesRates[0] = objectiveRate;
            this.bestSequence = this.currentSequence.copy();
            this.bestIteration = this.iterationCount;
        }
    }

    @Override
    protected boolean stop() {
        return this.iterationCount++ >= this.numberOfIterations;
    }

    public Sequence getBestSequence() {
        return this.bestSequence;
    }

    public double getBestObjectiveRate() {
        return this.bestObjectivesRates[0];
    }

    public int getBestIteration() {
        return this.bestIteration;
    }
}
