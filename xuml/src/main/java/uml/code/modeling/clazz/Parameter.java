package uml.code.modeling.clazz;

import java.util.ArrayList;

public class Parameter {
    private String mName;
    private String mType;

    public enum Direction {
        IN, OUT
    }

    private Direction mDirection;

    public Parameter(String name, String type) {
        this(name, type, Direction.IN);
    }

    public Parameter(String name, String type, Direction direction) {
        mName = name;
        mType = type;
        mDirection = direction;
    }

    public String getName() {
        return mName;
    }

    public String getType() {
        return mType;
    }
}
