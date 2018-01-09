package uml.x.statemachine;

import java.util.ArrayList;

public class Region implements EventHandler, ActiveNode {
    private final ArrayList<State> mStates = new ArrayList<>();
    private State mInitialState;
    private boolean mHistory;
    private State mLastEntered;

    public Region(State initialState) {
        this(initialState, false);
    }

    public Region(State initialState, boolean history) {
        mLastEntered = mInitialState = initialState;
        mHistory = history;
        addState(initialState);
    }

    @Override
    public void handle(Message message) {
        mStates.forEach(s -> s.handle(message));
    }

    @Override
    public void ensureExiting(Message message) {
        mStates.forEach(s -> s.ensureExiting(message));
    }

    public void entering(Message message) {
        if (!mHistory)
            mInitialState.entering(message);
        else
            mLastEntered.entering(message);
    }

    public void addState(State state) {
        mStates.add(state);
        state.addStateChangeListener(new StateChangeListener() {
            @Override
            public void onEntered(State source) {
                mLastEntered = source;
            }
        });
    }

    public void setInitialState(State initialState) {
        mInitialState = initialState;
    }
}
