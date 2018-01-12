package uml.code.modeling.clazz;

import java.util.ArrayList;

public class Operation {
    private final ArrayList<Parameter> mParameters = new ArrayList<>();
    private String mName;

    public Operation(String name) {
        mName = name;
    }

    public void addParameter(String name, String type, Parameter.Direction direction) {
        mParameters.add(new Parameter(name, type, direction));
    }

    public String getName() {
        return mName;
    }

    public ArrayList<Parameter> getParameters() {
        return new ArrayList<>(mParameters);
    }
}
