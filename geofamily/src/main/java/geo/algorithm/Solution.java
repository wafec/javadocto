package geo.algorithm;

public class Solution {
    private BinaryInteger candidate;
    private BinaryInteger actual;
    private int index;
    private int numberOfObjectives;
    private double[] objectivesRates;

    public Solution(BinaryInteger candidate, BinaryInteger actual, int index, int numberOfObjectives) {
        this.candidate = candidate;
        this.actual = actual;
        this.index = index;
        this.numberOfObjectives = numberOfObjectives;
        this.objectivesRates = new double[numberOfObjectives];
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
}
