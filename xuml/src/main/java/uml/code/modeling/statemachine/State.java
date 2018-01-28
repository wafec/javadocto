package uml.code.modeling.statemachine;

import java.util.ArrayList;

public class State {
    private String mName;
    private final ArrayList<Region> mRegions = new ArrayList<>();
    private final ArrayList<Transition> mTransitions = new ArrayList<>();

    public State(String name) {
        mName = name;
    }

    public void addRegion(Region region) {
        mRegions.add(region);
    }

    public void addTransition(Transition transition) {
        mTransitions.add(transition);
    }
}
