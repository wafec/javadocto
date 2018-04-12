package xstate.modeling;

import xstate.support.extending.PseudoNode;

// first state as a pseudo one is not affected essentially by performance issues
// onEntering only moves forward incoming messages
// but, if a transition is received, it will be processed at runtime (the worst case)
public class FirstState extends PseudoNode {
    public void addIncomingTransition(Transition transition) {
        addIncomingArrow(transition);
    }

    public void addOutgoingTransition(Transition transition) {
        addOutgoingArrow(transition);
    }
}
