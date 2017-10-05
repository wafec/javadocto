package geo.algorithm;

public class Solution {
    private BinaryInteger candidate;
    private BinaryInteger actual;
    private int index;
    private int bitFlipped;
    private int numberOfObjectives;
    private double[] objectivesRates;
    private int solutionIndex;
    private int kIndex;

    public Solution(BinaryInteger candidate, BinaryInteger actual, int index, int bitFlipped, int solutionIndex, int numberOfObjectives) {
        this.candidate = candidate;
        this.actual = actual;
        this.index = index;
        this.bitFlipped = bitFlipped;
        this.numberOfObjectives = numberOfObjectives;
        this.objectivesRates = new double[numberOfObjectives];
        this.solutionIndex = solutionIndex;
        this.kIndex = -1;
    }

    public void setObjectiveRate(int index, double rate) {
        this.objectivesRates[index] = rate;
    }

    public double getObjectiveRate(int index) {
        return this.objectivesRates[index];
    }

    public int getNumberOfObjectives() {
        return this.numberOfObjectives;
    }

    public BinaryInteger getActual() {
        return actual;
    }

    public BinaryInteger getCandidate() {
        return candidate;
    }

    public int getIndex() {
        return this.index;
    }

    public int getBitFlipped() {
        return this.bitFlipped;
    }

    public int getSolutionIndex() {
        return this.solutionIndex;
    }

    public void setK(int kIndex) {
        this.kIndex = kIndex;
    }

    public int getK() {
        return this.kIndex;
    }
}
