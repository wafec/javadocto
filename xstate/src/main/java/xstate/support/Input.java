package xstate.support;

import org.apache.log4j.Logger;
import xstate.support.extending.CodeSymbol;

import java.lang.reflect.Field;

public class Input {
    static Logger log = Logger.getLogger(Input.class);

    protected Symbol symbol;
    protected Args args;

    public Input(Symbol symbol, Args args) {
        this.symbol = symbol;
        this.args = args;
    }

    public Symbol getSymbol() {
        return symbol;
    }

    public Args getArgs() {
        return args;
    }

    public static <T> T createFrom(Input input, Class<T> clazz) {
        try {
            T instance = clazz.newInstance();
            Field[] fields = clazz.getFields();
            Args args = input.getArgs();
            for (int i = 0; i < Math.min(fields.length, args.getSize()); i++) {
                fields[i].set(instance, args.get(i));
            }
            return instance;
        } catch (InstantiationException | IllegalAccessException exception) {

        }
        return null;
    }

    public static <T> Input createTo(Object object, Class<T> clazz) {
        try {
            Field[] fields = clazz.getFields();
            Args args = new Args(fields.length);
            for (int i = 0; i < fields.length; i++) {
                args.set(i, fields[i].get(object));
            }
            return new Input(new CodeSymbol(clazz.hashCode()), args);
        } catch (IllegalAccessException exception) {

        }
        return null;
    }
}
