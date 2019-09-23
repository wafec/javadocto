package xstate.support;

public class Args {
    Object[] arguments;
    String[] parameters;

    public Args(int size) {
        arguments = new Object[size];
        parameters = new String[size];
    }

    public void set(int index, Object value) {
        set(index, value, null);
    }

    public void set(int index, Object value, String parameter) {
        arguments[index] = value;
        parameters[index] = parameter;
    }

    public int getSize() {
        return arguments.length;
    }

    public Object get(int index) {
        return arguments[index];
    }

    public String param(int index) {
        return parameters[index];
    }
}
