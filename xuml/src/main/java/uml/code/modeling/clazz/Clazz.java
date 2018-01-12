package uml.code.modeling.clazz;

import uml.code.modeling.ModelElement;
import uml.code.modeling.statemachine.StateDiagram;

import java.util.ArrayList;

public class Clazz extends ModelElement {
    private String mName;
    private String mFullPackage;
    private final ArrayList<Operation> mOperations = new ArrayList<>();
    private final ArrayList<Reception> mReceptions = new ArrayList<>();
    private StateDiagram mStateDiagram;

    public Clazz(String name, String fullPackage) {
        mName = name;
        mFullPackage = fullPackage;
    }

    public void addOperation(Operation operation) {
        mOperations.add(operation);
    }

    public void addReceptions(Reception reception) {
        mReceptions.add(reception);
    }

    public ArrayList<Operation> getOperations() {
        return new ArrayList(mOperations);
    }

    public ArrayList<Reception> getReceptions() {
        return new ArrayList(mReceptions);
    }

    public void defineStateDiagram(StateDiagram stateDiagram) {
        mStateDiagram = stateDiagram;
    }

    public StateDiagram getStateDiagram() {
        return mStateDiagram;
    }
}
