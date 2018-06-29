package geo.algorithm;

public class BinaryInteger {
    private int value;
    private int numberOfBits;

    public BinaryInteger(int value, int numberOfBits) {
        this.value = value;
        this.numberOfBits = numberOfBits;
    }

    public void flip(int index, BinaryInteger.Domain domain) {
        int gray = toGrayCode(this.value);
        int newValue = gray ^ (1 << index);
        newValue = toBinaryCode(newValue);
        if (newValue >= domain.getLowerBound() && newValue <= domain.getUpperBound()) {
            this.value = newValue;
        }
    }

    int toGrayCode(int code) {
        int res = 0;
        res = res | (code & (1 << numberOfBits - 1));
        for (int i = numberOfBits - 2; i >= 0; i--) {
            int bit1 = code & (1 << i);
            int bit0 = code & (1 << i + 1);
            int graybit = ((bit1 << 1) ^ bit0) >> 1;
            res = res | graybit;
        }
        return res;
    }

    int toBinaryCode(int code) {
        int res = 0;
        res = res | (code & (1 << numberOfBits - 1));
        for (int i = numberOfBits - 2; i >= 0; i--) {
            int bit1 = code & (1 << i);
            int graybit0 = res & (1 << i + 1);
            int binbit = ((bit1 << 1) ^ graybit0) >> 1;
            res = res | binbit;
        }
        return res;
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

    public static int calculateNumberOfBits(int lower, int upper) {
        int inter = Math.abs(lower - upper);
        return calculateNumberOfBits(inter);
    }

    public static int calculateNumberOfBits(int inter) {
        return (int) (Math.ceil(Math.log(inter) / Math.log(2)));
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
