package geo.algorithm;

import java.util.Arrays;
import java.util.Random;

public class Sequence {
    private BinaryInteger[] projectVariables;
    private BinaryInteger.Domain[] searchDomain;
    private Solution testSolution;

    public Sequence(BinaryInteger.Domain[] searchDomain) {
        this(null, searchDomain);
    }

    public Sequence(BinaryInteger[] projectVariables, BinaryInteger.Domain[] searchDomain) {
        this.projectVariables = projectVariables;
        this.searchDomain = searchDomain;
    }

    public BinaryInteger[] getProjectVariables() {
        return projectVariables;
    }

    public BinaryInteger.Domain[] getSearchDomain() {
        return this.searchDomain;
    }

    public void applySolution(Solution solution) {
        this.testSolution = solution;
        this.projectVariables[solution.getIndex()] = solution.getCandidate();
    }

    public void restore(Solution solution) {
        this.projectVariables[solution.getIndex()] = solution.getActual();
        this.testSolution = null;
    }

    public void sample(Random randomGenerator) {
        this.projectVariables = new BinaryInteger[this.searchDomain.length];
        for (int i = 0; i < this.searchDomain.length; i++) {
            BinaryInteger.Domain domain = this.searchDomain[i];
            this.projectVariables[i] = new BinaryInteger(
                    randomGenerator.nextInt(domain.getInterval()) + domain.getLowerBound(),
                    domain.getNumberOfBits()
            );
        }
    }

    public int getNumberOfProjectVariables() {
        return this.searchDomain.length;
    }

    public Sequence copy() {
        BinaryInteger[] otherProjectVariables = new BinaryInteger[getNumberOfProjectVariables()];
        for (int i = 0; i < otherProjectVariables.length; i++) {
            otherProjectVariables[i] = this.projectVariables[i].copy();
        }
        Sequence other = new Sequence(otherProjectVariables, this.searchDomain);
        return other;
    }

    public Sequence subSequence(int from, int to) {
        Sequence copyOf = copy();
        copyOf.projectVariables = Arrays.copyOfRange(copyOf.projectVariables, from, to);
        copyOf.searchDomain = Arrays.copyOfRange(copyOf.searchDomain, from, to);
        return copyOf;
    }

    public Solution getTestSolution() {
        return testSolution;
    }
}
