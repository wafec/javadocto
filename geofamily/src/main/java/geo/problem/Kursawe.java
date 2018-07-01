package geo.problem;

import geo.algorithm.BinaryInteger;
import geo.algorithm.Objective;
import geo.algorithm.Sequence;

public class Kursawe {
    public final static int decimalPlaces = 7;
    public final static int lowerBound = 0;
    public final static int upperBound = (int) (1 * Math.pow(10, decimalPlaces + 1));
    public final static int numberOfBits = (int) (Math.ceil(Math.log(upperBound) / Math.log(2)));
    public final static BinaryInteger.Domain[] searchDomain = new BinaryInteger.Domain[] {
            new BinaryInteger.Domain(lowerBound, upperBound),
            new BinaryInteger.Domain(lowerBound, upperBound),
            new BinaryInteger.Domain(lowerBound, upperBound)
    };

    private final static double getValue(int i, Sequence sequence) {
        int v = sequence.getProjectVariables()[i].getValue() - upperBound / 2;
        return v / Math.pow(10, decimalPlaces);
    }

    public final static double getX1(Sequence sequence) {
        return getValue(0, sequence);
    }

    public final static double getX2(Sequence sequence) {
        return getValue(1, sequence);
    }

    public final static double getX3(Sequence sequence) {
        return getValue(2, sequence);
    }

    public static class ObjectiveOne implements Objective {
        @Override
        public double eval(Object object) {
            Sequence sequence = (Sequence) object;
            double x1 = getX1(sequence);
            double x2 = getX2(sequence);
            double x3 = getX3(sequence);
            double[] xs = new double[] { x1, x2, x3 };
            double fx = 0;
            for (int i = 0; i < 2; i++) {
                fx += -10.0 * Math.exp(-0.2 * Math.sqrt(Math.pow(xs[i], 2) + Math.pow(xs[i + 1], 2)));
            }
            return fx;
        }
    }

    public static class ObjectiveTwo implements Objective {
        @Override
        public double eval(Object object) {
            Sequence sequence = (Sequence) object;
            double x1 = getX1(sequence);
            double x2 = getX2(sequence);
            double x3 = getX3(sequence);
            double[] xs = new double[] { x1, x2, x3 };
            double fx = 0;
            for (int i = 0; i < 3; i++) {
                fx += Math.pow(Math.abs(xs[i]), 0.8) + 5.0 * Math.sin(Math.pow(xs[i], 3.0));
            }
            return fx;
        }
    }
}
