package statemutest.meter;

public class GenericMeasure {
    public double ratio;

    public void setRatio(double total, double real) {
        if (real == 0)
            ratio = 0;
        else {
            ratio = real / total;
        }
    }
}
