package uml.x.statemachine;

import java.util.ArrayList;

public class Region implements EventHandler {
    private final ArrayList<State> mStates = new ArrayList<>();
    private State mInitialState;

    public Region(State initialState) {
        mInitialState = initialState;
        addState(initialState);
    }

    @Override
    public void handle(Message message) {
        mStates.forEach(s -> s.handle(message));
    }

    public void entering(Message message) {
        mInitialState.entering(message);
    }

    public void addState(State state) {
        mStates.add(state);
    }

    public void setInitialState(State initialState) {
        mInitialState = initialState;
    }
}
