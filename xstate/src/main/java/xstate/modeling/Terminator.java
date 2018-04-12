package xstate.modeling;

import xstate.support.Node;

public class Terminator extends Node {
    public void addIncomingTransition(Transition transition) {
        incomingArrows.add(transition);
    }
}
