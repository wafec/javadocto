package xstate.modeling;

import xstate.support.Input;
import xstate.support.Node;
import xstate.support.Output;

import java.util.ArrayList;

public class State extends Node {
    String name = "undefined";
    ArrayList<Output> doEntry = new ArrayList<>();
    ArrayList<Output> doExit = new ArrayList<>();

    public State() {}

    public State(String name) {
        this.name = name;
    }

    public void addSubRegion(Region region) {
        addChild(region);
        addStartingNode(region);
    }

    public void addOutgoingTransition(Transition transition) {
        addOutgoingArrow(transition);
    }

    public void addIncomingTransition(Transition transition) {
        addIncomingArrow(transition);
    }

    public void setName(String name) {
        this.name = name;
    }

    public void addEntry(Output output) {
        if (!doEntry.contains(output)) {
            doEntry.add(output);
        }
    }

    public void addExit(Output output) {
        if (!doExit.contains(output)) {
            doExit.add(output);
        }
    }

    @Override
    protected void onEntry(Input input) {
        doEntry.stream().forEach(o -> o.run(input));
    }

    @Override
    protected void onExit(Input input) {
        doExit.stream().forEach(o -> o.run(input));
    }

    @Override
    public String toString() {
        return "[State " + name + "]";
    }
}
