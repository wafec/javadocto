package xstate.modeling;

import xstate.support.Arrow;
import xstate.support.Input;
import xstate.support.Node;

public class Choice extends Node {
    public void addOutgoingTransition(Transition transition) {
        addOutgoingArrow(transition);
    }

    public void addIncomingTransition(Transition transition) {
        addIncomingArrow(transition);
    }

    @Override
    public boolean onTransit(Input input) {
        active = true;
        boolean res = onInput(input);
        active = false;
        // return false, onExiting already ensures that source will be exited
        // onEntering is a problem if called recursively, will activate exited ones
        // false makes it stop (don't call onExiting and onEntering from arrows)
        // this limits choice nodes be called from the source hierarchy level only
        return res && false;
    }

    @Override
    public void onExiting(Input input) {
        incomingArrows.stream().filter(a -> a.getState() == Arrow.States.IN_TRANSIT).forEach(a -> {
            a.getSource().onExiting(input);
        });
    }

    @Override
    public void onEntering(Input input, boolean inDepth) {

    }
}
