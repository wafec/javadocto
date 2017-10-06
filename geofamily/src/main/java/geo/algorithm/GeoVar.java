package geo.algorithm;

import java.util.Arrays;

public class GeoVar extends Geo {
    public GeoVar(double tau, int numberOfIterations, Objective objective, BinaryInteger.Domain[] searchDomain) {
        super(tau, numberOfIterations, objective, searchDomain);
    }

    @Override
    protected void sortCandidatesSolutions() {
        final double bestRate = this.bestObjectivesRates[0];
        int solutionIndex = 0;
        for (int i = 0; i < this.searchDomain.length; i++) {
            BinaryInteger.Domain domain = this.searchDomain[i];
            Solution[] vSolution = new Solution[domain.getNumberOfBits()];
            for (int j = 0; j < domain.getNumberOfBits(); j++) {
                vSolution[j] = this.currentSolutions[solutionIndex++];
            }
            Arrays.sort(vSolution, (solution1, solution2) -> {
                double rate1 = solution1.getObjectiveRate(0) - bestRate;
                double rate2 = solution2.getObjectiveRate(0) - bestRate;
                return Double.compare(rate1, rate2);
            });
            for (int k = 0; k < vSolution.length; k++) {
                vSolution[k].setK(k + 1);
            }
        }
    }

    @Override
    protected void chooseCandidateSolution() {
        int solutionIndex = 0;
        int[] changes = new int[this.searchDomain.length];
        for (int i = 0; i < this.searchDomain.length; i++) {
            BinaryInteger.Domain domain = this.searchDomain[i];
            double n;
            int si;
            int k;
            double c;
            do {
                si = this.randomGenerator.nextInt(domain.getNumberOfBits());
                n = this.randomGenerator.nextDouble();
                k = this.currentSolutions[solutionIndex + si].getK();
                c = Math.pow(k, -this.tau);
            } while(n > c);
            changes[i] = solutionIndex + si;
            solutionIndex += domain.getNumberOfBits();
        }
        for (int i = 0; i < changes.length; i++) {
            this.currentSequence.applySolution(this.currentSolutions[changes[i]]);
        }
        this.calculateCurrentObjectivesRates();
    }
}
