package xstate.modeling;

import xstate.support.Arrow;
import xstate.support.Input;
import xstate.support.Node;

public class FirstState extends Node {
    public void addIncomingTransition(Transition transition) {
        addIncomingArrow(transition);
    }

    public void addOutgoingTransition(Transition transition) {
        addOutgoingArrow(transition);
    }

    @Override
    public void onEntering(Input input, boolean inDepth) {
        active = true;
        onInput(input);
        active = false;
    }

    @Override
    public void onExiting(Input input) {
        incomingArrows.stream().filter(a -> a.getState() == Arrow.States.IN_TRANSIT).forEach(a -> {
            a.getSource().onExiting(input);
        });
    }
}
