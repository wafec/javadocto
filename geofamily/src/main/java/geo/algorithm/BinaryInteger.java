package geo.algorithm;

public class BinaryInteger {
    private int value;
    private int numberOfBits;

    public BinaryInteger(int value, int numberOfBits) {
        this.value = value;
        this.numberOfBits = numberOfBits;
    }

    public void flip(int index) {

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
}
