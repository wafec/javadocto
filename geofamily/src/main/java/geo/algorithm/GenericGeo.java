package geo.algorithm;

public abstract class GenericGeo extends Algorithm {
    protected Sequence currentSequence;
    protected double[] bestObjectivesRates;
    protected Objective[] objectives;
    protected BinaryInteger.Domain[] domains;
    protected Solution[] currentSolutions;
    protected int totalOfBits;

    public GenericGeo(Objective[] objectives, BinaryInteger.Domain[] domains) {
        this.objectives = objectives;
        this.domains = domains;
        this.totalOfBits = BinaryInteger.Domain.computeTotalOfBits(domains);
    }

    @Override
    protected void initialization() {
        this.currentSequence = new Sequence(this.domains);
        this.currentSequence.sample();
        this.bestObjectivesRates = new double[this.objectives.length];
        for (int i = 0; i < objectives.length; i++) {
            this.bestObjectivesRates[i] = this.objectives[i].eval(this.currentSequence);
        }
    }

    @Override
    protected void doMutation() {
        this.currentSolutions = new Solution[this.totalOfBits];
        int solutionIndex = 0;
        for (int i = 0; i < this.currentSequence.getNumberOfProjectVariables(); i++) {
            BinaryInteger projectVariable = this.currentSequence.getProjectVariables()[i];
            for (int j = 0; j < projectVariable.getNumberOfBits(); j++) {
                BinaryInteger candidate = projectVariable.copy();
                candidate.flip(j);
                Solution solution = new Solution(
                        candidate,
                        projectVariable,
                        i,
                        j,
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
}
