package knowledge.util;

public class DistanceMath {
    public static int or(int a, int b) {
        return Math.min(a, b);
    }

    public static int and(int a, int b) {
        return a + b;
    }

    public static int lessThan(int a, int b) {
        return positive(a - b + 1);
    }

    public static int greaterThan(int a, int b) {
        return positive(b - a + 1);
    }

    public static int lessOrEqualThan(int a, int b) {
        return positive(a - b);
    }

    public static int greaterOrEqualThan(int a, int b) {
        return positive(b - a);
    }

    public static int equalThan(int a, int b) {
        return Math.abs(a - b);
    }

    public static int notEqualThan(int a, int b) {
        return a == b ? 1 : 0;
    }

    public static int positive(int a) {
        if (a > 0) {
            return a;
        }
        return a;
    }
}
