package geo.problem;

import geo.algorithm.BinaryInteger;
import geo.algorithm.Objective;
import geo.algorithm.Sequence;

public class Booth {
    public static final int numberOfBits = (int)(Math.ceil(Math.log(20) / Math.log(2)));
    public static final BinaryInteger.Domain[] searchDomain = new BinaryInteger.Domain[] {
            new BinaryInteger.Domain(0, 20, numberOfBits),
            new BinaryInteger.Domain(0, 20, numberOfBits)
    };

    public static class ObjectiveOne implements Objective {
        @Override
        public double eval(Object object) {
            Sequence sequence = (Sequence) object;
            int x = sequence.getProjectVariables()[0].getValue() - 10;
            int y = sequence.getProjectVariables()[1].getValue() - 10;
            double dx = x / 1.0;
            double dy = y / 1.0;
            double fx = Math.pow((dx + 2 * dy - 7), 2) + Math.pow((2 * dx + dy - 5), 2);
            return fx;
        }
    }
}
