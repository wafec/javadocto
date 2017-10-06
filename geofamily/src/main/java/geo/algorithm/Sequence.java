package geo.algorithm;

import java.util.Random;

public class Sequence {
    private BinaryInteger[] projectVariables;
    private BinaryInteger.Domain[] domains;

    public Sequence(BinaryInteger.Domain[] domains) {
        this(null, domains);
    }

    public Sequence(BinaryInteger[] projectVariables, BinaryInteger.Domain[] domains) {
        this.projectVariables = projectVariables;
        this.domains = domains;
    }

    public BinaryInteger[] getProjectVariables() {
        return projectVariables;
    }

    public BinaryInteger.Domain[] getDomains() {
        return this.domains;
    }

    public void applySolution(Solution solution) {
        this.projectVariables[solution.getIndex()] = solution.getCandidate();
    }

    public void restore(Solution solution) {
        this.projectVariables[solution.getIndex()] = solution.getActual();
    }

    public void sample(Random randomGenerator) {
        this.projectVariables = new BinaryInteger[this.domains.length];
        for (int i = 0; i < this.domains.length; i++) {
            BinaryInteger.Domain domain = this.domains[i];
            this.projectVariables[i] = new BinaryInteger(
                    randomGenerator.nextInt(domain.getInterval()) + domain.getLowerBound(),
                    domain.getNumberOfBits()
            );
        }
    }

    public int getNumberOfProjectVariables() {
        return this.domains.length;
    }

    public Sequence copy() {
        BinaryInteger[] otherProjectVariables = new BinaryInteger[getNumberOfProjectVariables()];
        for (int i = 0; i < otherProjectVariables.length; i++) {
            otherProjectVariables[i] = this.projectVariables[i].copy();
        }
        Sequence other = new Sequence(otherProjectVariables, this.domains);
        return other;
    }
}
