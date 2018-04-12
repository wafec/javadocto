package xstate.modeling;

import xstate.support.extending.PseudoNode;

public class Choice extends PseudoNode {
    public void addOutgoingTransition(Transition transition) {
        addOutgoingArrow(transition);
    }

    public void addIncomingTransition(Transition transition) {
        addIncomingArrow(transition);
    }
}
