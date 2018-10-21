package xstate.modeling;

import xstate.support.Input;
import xstate.support.Node;
import xstate.support.Output;

import java.util.ArrayList;

public class Region extends Node {
    ArrayList<Output> doEntry = new ArrayList<>();
    ArrayList<Output> doExit = new ArrayList<>();

    public void setFirstState(FirstState firstState) {
        setJustOneStartingNode(firstState);
    }

    public void addState(State state) {
        addChild(state);
    }

    public void addFinalState(Terminator terminator) {
        addChild(terminator);
    }

    public void addChoice(Choice choice) {
        addChild(choice);
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
}
