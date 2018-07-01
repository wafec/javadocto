package geo.algorithm;

import java.util.Arrays;
import java.util.Comparator;

public class Geo extends GenericGeo {
    protected Sequence bestSequence;
    protected int numberOfIterations;
    protected int iterationCount;
    protected int bestIteration;

    protected int bestObjectivesRatesIndex;

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
        // multiple objectives require this
        bestObjectivesRatesIndex = randomGenerator.nextInt(this.bestObjectivesRates.length);
        final double bestRate = this.bestObjectivesRates[bestObjectivesRatesIndex];
        Arrays.sort(this.currentSolutions, (solution1, solution2) -> {
            double rate1 = solution1.getObjectiveRate(bestObjectivesRatesIndex) - bestRate;
            double rate2 = solution2.getObjectiveRate(bestObjectivesRatesIndex) - bestRate;
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
            // tau in action
            c = Math.pow(k, -this.tau);
        } while(n > c);

        this.currentSequence.applySolution(this.currentSolutions[i]);
        this.calculateCurrentObjectivesRates();
    }

    @Override
    protected void update() {
        double objectiveRate = this.objectives[bestObjectivesRatesIndex].eval(this.currentSequence);
        if (objectiveRate < this.bestObjectivesRates[bestObjectivesRatesIndex]) {
            this.bestObjectivesRates[bestObjectivesRatesIndex] = objectiveRate;
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

    // according to a run
    public double getBestObjectiveRate() {
        return this.bestObjectivesRates[bestObjectivesRatesIndex];
    }

    public int getBestIteration() {
        return this.bestIteration;
    }
}
