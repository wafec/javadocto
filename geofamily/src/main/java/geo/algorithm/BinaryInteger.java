package geo.algorithm;

public class BinaryInteger {
    private int value;
    private int numberOfBits;

    public BinaryInteger(int value, int numberOfBits) {
        this.value = value;
        this.numberOfBits = numberOfBits;
    }

    public void flip(int index, BinaryInteger.Domain domain) {
        int newValue = this.value ^ (1 << index);
        if (newValue >= domain.getLowerBound() && newValue <= domain.getUpperBound()) {
            this.value = newValue;
        }
    }

    public BinaryInteger copy() {
        BinaryInteger other = new BinaryInteger(this.value, this.numberOfBits);
        return other;
    }

    public int getValue() {
        return this.value;
    }

    public int getNumberOfBits() {
        return this.numberOfBits;
    }

    public void setValue(int value) {
        this.value = value;
    }

    public void setNumberOfBits(int numberOfBits) {
        this.numberOfBits = numberOfBits;
    }

    public static class Domain {
        private int lowerBound;
        private int upperBound;
        private int numberOfBits;

        public Domain(int lowerBound, int upperBound, int numberOfBits) {
            this.lowerBound = lowerBound;
            this.upperBound = upperBound;
            this.numberOfBits = numberOfBits;
        }

        public int getLowerBound() {
            return this.lowerBound;
        }

        public int getUpperBound() {
            return this.upperBound;
        }

        public int getNumberOfBits() {
            return this.numberOfBits;
        }

        public int getInterval() {
            return this.upperBound - this.lowerBound;
        }

        public static int computeTotalOfBits(Domain[] domains) {
            int count = 0;
            for (int i = 0; i < domains.length; i++) {
                count += domains[i].getNumberOfBits();
            }
            return count;
        }
    }
}
