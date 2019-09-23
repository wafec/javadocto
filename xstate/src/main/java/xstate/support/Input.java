package xstate.support;

import org.apache.commons.lang3.StringUtils;
import org.apache.log4j.Logger;
import xstate.support.extending.CodeSymbol;

import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class Input {
    static Logger log = Logger.getLogger(Input.class);

    protected Symbol symbol;
    protected Args args;
    protected Class source;

    public Input(Symbol symbol, Args args) {
        this(symbol, args, null);
    }

    public Input(Symbol symbol, Args args, Class source) {
        this.symbol = symbol;
        this.args = args;
        this.source = source;
    }

    public Symbol getSymbol() {
        return symbol;
    }

    public Args getArgs() {
        return args;
    }

    public Class getSourceDescription() {
        return source;
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
                args.set(i, fields[i].get(object), fields[i].getName());
            }
            return new Input(new CodeSymbol(clazz.hashCode()), args, clazz);
        } catch (IllegalAccessException exception) {

        }
        return null;
    }

    @Override
    public String toString() {
        String description = symbol.toString();
        if (source != null)
            description = source.getCanonicalName();
        String arg = "";
        if (args != null && args.arguments != null && args.arguments.length > 0) {
            List<String> argList = new ArrayList<>();
            for (int i = 0; i < args.getSize(); i++) {
                Object value = args.get(i);
                String param = args.param(i);
                if (!StringUtils.isEmpty(param))
                    argList.add(String.format("%s: %s", param, value));
                else
                    argList.add(String.format("%s", value));
            }
            arg = String.format("(%s)", String.join(", ", argList));
        }
        return String.format("%s%s", description, arg);
    }
}
