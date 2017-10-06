package geo.algorithm;

public class MgeoVsl extends Mgeo {
    public MgeoVsl(double tau, int numberOfIterations, int numberOfIndependentRuns,
                   Objective[] objectives, BinaryInteger.Domain[] searchDomain) {
        super(tau, numberOfIterations, numberOfIndependentRuns, objectives, searchDomain);
    }

    public static class Sequence extends geo.algorithm.Sequence {
        public Sequence(BinaryInteger[] fixedChain, BinaryInteger[] variableChain,
                        BinaryInteger.Domain[] fixedSearchDomain, BinaryInteger.Domain variableSearchDomain,
                        int maxVariableChainSize) {
            super(projectVariables, searchDomain);
        }

        public Sequence(BinaryInteger.Domain[] searchDomain) {
            super(searchDomain);
        }
    }

    protected static class Objective implements geo.algorithm.Objective {
        private geo.algorithm.Objective realObjective;

        public Objective(geo.algorithm.Objective realObjective) {
            this.realObjective = realObjective;
        }

        @Override
        public double eval(Object object) {
            Sequence sequence = (Sequence) object;
            return this.realObjective.eval(sequence);
        }
    }
}
