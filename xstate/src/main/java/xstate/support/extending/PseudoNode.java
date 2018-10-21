package xstate.support.extending;

import xstate.support.Arrow;
import xstate.support.Input;
import xstate.support.Node;

import java.util.stream.Collectors;

// never be active
public class PseudoNode extends Node {
    @Override
    public boolean onTransit(Input input, Arrow from) {
        getOutgoingArrows().stream().forEach(a -> {
            // heavy operation performed here
            // pseudo-none should be avoided as possible
            // diff calculation is made at runtime
            // direct transitions are better in performance as they are calculated at building time
            a.setSource(from.getSource());
            a.updateDiff();
            a.transit(input);
            a.setSource(this);
            a.updateDiff();
        });
        return false;
    }

    @Override
    public void onExiting(Input input) {
        // if called (recommended does not call this)
        // forward back to incoming callers
        incomingArrows.stream().filter(a -> a.getState() == Arrow.States.IN_TRANSIT)
                .collect(Collectors.toList())
                .forEach(a -> {
                    a.getSource().onExiting(input);
                });
    }

    @Override
    public void onEntering(Input input, boolean inDepth) {
        // inDepth: never used
        // pseudo-nodes don't have children
        // onEntering is ever forwarded
        getOutgoingArrows().stream().forEach(a -> {
            a.transit(input);
        });
    }
}
