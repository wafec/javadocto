package uml.x.statemachine;

import java.util.ArrayList;

public class State implements EventHandler {
    protected final ArrayList<Region> mRegions = new ArrayList<>();
    protected final ArrayList<Transition> mTransitions = new ArrayList<>();
    protected boolean mIsActive = false;
    protected Action mEntry = Action.DEFAULT;
    protected Action mExit = Action.DEFAULT;

    @Override
    public void handle(Message message) {
        if (!mIsActive) {
            return;
        }
        mRegions.forEach(r -> r.handle(message));
        for (Transition t : mTransitions) {
            if (t.eval(message))
                doTransition(message, t);
                break;
        }
    }

    protected void doTransition(Message message, Transition transition) {
        exit(message);
        transition.act(message);
        transition.go(message);
    }

    public void entering(Message message) {
        entry(message);
        mRegions.forEach(r -> r.entering(message));
    }

    protected void entry(Message message) {
        mEntry.run(message);
        mIsActive = true;
    }

    protected void exit(Message message) {
        mExit.run(message);
        mIsActive = false;
    }

    public void addRegion(Region region) {
        mRegions.add(region);
    }

    public void setEntry(Action entry) {
        mEntry = entry;
    }

    public void setExit(Action exit) {
        mExit = exit;
    }

    public void addTransition(Transition transition) {
        mTransitions.add(transition);
    }

    public boolean isActive() {
        return mIsActive;
    }
}
