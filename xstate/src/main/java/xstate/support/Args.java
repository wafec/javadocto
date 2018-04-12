package xstate.support;

public class Args {
    Object[] arguments;

    public Args(int size) {
        arguments = new Object[size];
    }

    public void set(int index, Object value) {
        arguments[index] = value;
    }

    public int getSize() {
        return arguments.length;
    }

    public Object get(int index) {
        return arguments[index];
    }
}
