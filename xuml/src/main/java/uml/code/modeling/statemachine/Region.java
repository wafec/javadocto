package uml.code.modeling.statemachine;

import java.util.ArrayList;

public class Region {
    private String mName;
    private final ArrayList<State> mStates = new ArrayList<>();

    public Region(String name) {
        mName = name;
    }

    public void addState(State state) {
        mStates.add(state);
    }
}
