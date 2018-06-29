package geo.algorithm;

import java.util.Arrays;

public class Mgeo extends Geo {
    protected ParetoFrontier paretoFrontier;
    protected int objectiveIndex;
    protected int numberOfIndependentRuns;

    public Mgeo(double tau, int numberOfIterations, int numberOfIndependentRuns,
                Objective[] objectives, BinaryInteger.Domain[] searchDomain) {
        super(tau, numberOfIterations, null, searchDomain);
        this.objectives = objectives;
        this.numberOfIndependentRuns = numberOfIndependentRuns;
    }

    @Override
    protected void initialization() {
        super.initialization();
        this.paretoFrontier = new ParetoFrontier();
        Sequence copyOfSequence = this.currentSequence.copy();
        double[] copyOfCurrentObjectivesRates = Arrays.copyOfRange(this.currentObjectivesRates, 0, this.currentObjectivesRates.length);
        this.paretoFrontier.add(copyOfSequence, copyOfCurrentObjectivesRates, 0);
    }

    protected void reinitialization() {
        int copyOfIterationCount = this.iterationCount;
        super.initialization();
        this.iterationCount = copyOfIterationCount;
    }

    protected void doReinitializationIf() {
        if (this.iterationCount % (this.numberOfIterations / this.numberOfIndependentRuns) == 0) {
            reinitialization();
        }
    }


    @Override
    protected void sortCandidatesSolutions() {
        this.objectiveIndex = this.randomGenerator.nextInt(this.objectives.length);
        double tmp = this.bestObjectivesRates[0];
        this.bestObjectivesRates[0] = this.bestObjectivesRates[this.objectiveIndex];
        super.sortCandidatesSolutions();
        this.bestObjectivesRates[this.objectiveIndex] = this.bestObjectivesRates[0];
        this.bestObjectivesRates[0] = tmp;
    }

    protected void updateBestObjectivesRates() {
        for (int i = 0; i < this.bestObjectivesRates.length; i++) {
            if (this.currentObjectivesRates[i] < this.bestObjectivesRates[i]) {
                this.bestObjectivesRates[i] = this.currentObjectivesRates[i];
            }
        }
    }

    @Override
    protected void update() {
        Sequence copyOfSequence = this.currentSequence.copy();
        double[] copyOfCurrentObjectivesRates = Arrays.copyOfRange(this.currentObjectivesRates, 0, this.currentObjectivesRates.length);
        System.arraycopy(this.currentObjectivesRates, 0, copyOfCurrentObjectivesRates, 0, copyOfCurrentObjectivesRates.length);
        if (this.paretoFrontier.add(copyOfSequence, copyOfCurrentObjectivesRates, this.iterationCount)) {
            this.updateBestObjectivesRates();
        }
    }

    @Override
    protected boolean stop() {
        if (this.iterationCount > 0 && this.iterationCount < this.numberOfIterations - 1) {
            doReinitializationIf();
        }
        return super.stop();
    }

    public ParetoFrontier getParetoFrontier() {
        return paretoFrontier;
    }
}
