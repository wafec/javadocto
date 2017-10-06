package geo.algorithm;

import java.util.Random;

public abstract class GenericGeo extends Algorithm {
    protected Sequence currentSequence;
    protected double[] currentObjectivesRates;
    protected double[] bestObjectivesRates;
    protected Objective[] objectives;
    protected BinaryInteger.Domain[] searchDomain;
    protected Solution[] currentSolutions;
    protected int totalOfBits;
    protected Random randomGenerator;

    public GenericGeo(double tau, Objective[] objectives, BinaryInteger.Domain[] searchDomain) {
        super(tau);
        this.objectives = objectives;
        this.searchDomain = searchDomain;
        this.totalOfBits = BinaryInteger.Domain.computeTotalOfBits(this.searchDomain);
        this.randomGenerator = new Random();
    }

    @Override
    protected void initialization() {
        this.currentSequence = new Sequence(this.searchDomain);
        this.currentSequence.sample(this.randomGenerator);
        this.bestObjectivesRates = new double[this.objectives.length];
        for (int i = 0; i < objectives.length; i++) {
            this.bestObjectivesRates[i] = this.objectives[i].eval(this.currentSequence);
        }
        this.currentObjectivesRates = new double[this.objectives.length];
        System.arraycopy(this.currentObjectivesRates, 0, this.bestObjectivesRates, 0, this.bestObjectivesRates.length);
    }

    @Override
    protected void doMutation() {
        this.currentSolutions = new Solution[this.totalOfBits];
        int solutionIndex = 0;
        for (int i = 0; i < this.currentSequence.getNumberOfProjectVariables(); i++) {
            BinaryInteger projectVariable = this.currentSequence.getProjectVariables()[i];
            for (int j = 0; j < projectVariable.getNumberOfBits(); j++) {
                BinaryInteger candidate = projectVariable.copy();
                candidate.flip(j, this.searchDomain[i]);
                Solution solution = new Solution(
                        candidate,
                        projectVariable,
                        i,
                        j,
                        solutionIndex,
                        this.objectives.length
                );
                this.currentSequence.applySolution(solution);
                for (int k = 0; k < this.objectives.length; k++) {
                    solution.setObjectiveRate(k, this.objectives[k].eval(this.currentSequence));
                }
                this.currentSequence.restore(solution);
                this.currentSolutions[solutionIndex++] = solution;
            }
        }
    }

    protected void calculateCurrentObjectivesRates() {
        for (int i = 0; i < this.objectives.length; i++) {
            this.currentObjectivesRates[i] = this.objectives[i].eval(this.currentSequence);
        }
    }
}
