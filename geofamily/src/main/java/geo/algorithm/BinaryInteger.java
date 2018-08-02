package geo.algorithm;

public class BinaryInteger {
    private int value;
    private BinaryInteger.Domain domain;

    public BinaryInteger(int value, BinaryInteger.Domain domain) {
        domain.validate(value, true);
        this.value = value;
        this.domain = domain;

    }

    public void flip(int index) {
        int gray = toGrayCode(this.value);
        int newValue = gray ^ (1 << index);
        newValue = toBinaryCode(newValue);
        if (domain.validate(newValue)) {
            this.value = newValue;
        }
    }

    int toGrayCode(int code) {
        int res = 0;
        res = res | (code & (1 << domain.numberOfBits - 1));
        for (int i = domain.numberOfBits - 2; i >= 0; i--) {
            int bit1 = code & (1 << i);
            int bit0 = code & (1 << i + 1);
            int graybit = ((bit1 << 1) ^ bit0) >> 1;
            res = res | graybit;
        }
        return res;
    }

    int toBinaryCode(int code) {
        int res = 0;
        res = res | (code & (1 << domain.numberOfBits - 1));
        for (int i = domain.numberOfBits - 2; i >= 0; i--) {
            int bit1 = code & (1 << i);
            int graybit0 = res & (1 << i + 1);
            int binbit = ((bit1 << 1) ^ graybit0) >> 1;
            res = res | binbit;
        }
        return res;
    }

    public BinaryInteger copy() {
        BinaryInteger other = new BinaryInteger(this.value, this.domain);
        return other;
    }

    public int getValue() {
        return domain.lowerBound + this.value;
    }

    public int getNumberOfBits() {
        return this.domain.numberOfBits;
    }

    public void setValue(int value) {
        domain.validate(value, true);
        this.value = value;
    }

    public static class Domain {
        private int lowerBound;
        private int upperBound;
        private int numberOfBits;

        public Domain(int lowerBound, int upperBound) {
            this.lowerBound = lowerBound;
            this.upperBound = upperBound;
            this.numberOfBits = calculateNumberOfBits(lowerBound, upperBound);
        }

        Domain() {

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

        boolean validate(int value) {
            return validate(value, false);
        }

        boolean validate(int value, boolean raiseException) {
            value += lowerBound;
            if (!(value >= lowerBound && value <= upperBound)) {
                if (raiseException)
                    throw new IllegalArgumentException("Value " + value + " must be between " + lowerBound + " and " + upperBound);
                return false;
            }
            return true;
        }

        public static int calculateNumberOfBits(int lower, int upper) {
            int inter = Math.abs(lower - upper) + 1;
            return calculateNumberOfBits(inter);
        }

        public static int calculateNumberOfBits(int inter) {
            return (int) (Math.ceil(Math.log(inter) / Math.log(2)));
        }

        public Domain clone() {
            Domain newInstance = new Domain();
            newInstance.lowerBound = lowerBound;
            newInstance.upperBound = upperBound;
            newInstance.numberOfBits = numberOfBits;
            return newInstance;
        }
    }
}
