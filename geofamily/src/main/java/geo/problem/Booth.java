package geo.problem;

import geo.algorithm.BinaryInteger;
import geo.algorithm.Objective;
import geo.algorithm.Sequence;

public class Booth {
    public static final int decimalPlaces = 1;
    private static final int upperBound = (int)(2 * Math.pow(10, decimalPlaces + 1));
    public static final int numberOfBits = (int)(Math.ceil(Math.log(upperBound) / Math.log(2)));
    public static final BinaryInteger.Domain[] searchDomain = new BinaryInteger.Domain[] {
            new BinaryInteger.Domain(0, upperBound, numberOfBits),
            new BinaryInteger.Domain(0, upperBound, numberOfBits)
    };

    public static double getX(Sequence sequence) {
        int x = sequence.getProjectVariables()[0].getValue() - upperBound / 2;
        double dx = x / Math.pow(10, decimalPlaces);
        return dx;
    }

    public static double getY(Sequence sequence) {
        int y = sequence.getProjectVariables()[1].getValue() - upperBound / 2;
        double dy = y / Math.pow(10, decimalPlaces);
        return dy;
    }

    public static class ObjectiveOne implements Objective {
        @Override
        public double eval(Object object) {
            Sequence sequence = (Sequence) object;
            double dx = getX(sequence);
            double dy = getY(sequence);
            double fx = Math.pow((dx + 2 * dy - 7), 2) + Math.pow((2 * dx + dy - 5), 2);
            return fx;
        }
    }
}
