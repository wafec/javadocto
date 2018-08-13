package statemutest.meter;

public abstract class PairBasedCoverage extends AbstractCoverage {
    public static class Pair {
        public String instanceA;
        public String instanceB;

        boolean isStrEqual(String a, String b) {
            if (a == null && b != null)
                return false;
            if (a != null && b == null)
                return false;
            if (a == null && b == null)
                return true;
            return a.equals(b);
        }

        @Override
        public boolean equals(Object other) {
            if (other instanceof Pair) {
                Pair otherPair = (Pair) other;
                return isStrEqual(instanceA, otherPair.instanceA) &&
                        isStrEqual(instanceB, otherPair.instanceB);
            }
            return super.equals(other);
        }

        @Override
        public int hashCode() {
            if (instanceB == null)
                return instanceA.hashCode();
            if (instanceA == null)
                return instanceB.hashCode();
            if (instanceB == null && instanceA == null)
                return super.hashCode();
            return instanceA.hashCode() + instanceB.hashCode();
        }

        @Override
        public String toString() {
            return "instanceA=" + instanceA + ", instanceB=" + instanceB;
        }
    }
}
