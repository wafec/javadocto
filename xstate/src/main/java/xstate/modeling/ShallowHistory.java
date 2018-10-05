package xstate.modeling;

import xstate.support.Arrow;
import xstate.support.Node;

import java.util.Arrays;
import java.util.List;

public class ShallowHistory extends FirstState {
    Node activeNode;
    public static final String SHALLOW_TRANSITION_ID = "__SHALLOW_T_";

    @Override
    protected void parentUpdatingChildCuzOfChildChange(Node child, String[] changes) {
        List listChanges = Arrays.asList(changes);
        if (listChanges.contains("active")) {
            if (child.isActive()) {
                activeNode = child;
                updatingOutgoingTransition();
            }
        }
    }

    void updatingOutgoingTransition() {
        if (outgoingArrows != null) {
            for (Arrow arrow : outgoingArrows) {
                arrow.getDestination().removeIncomingArrow(arrow);
            }
            outgoingArrows.clear();
            Arrow arrow = new Arrow();
            arrow.setSource(this);
            arrow.setDestination(activeNode);
            arrow.setId(SHALLOW_TRANSITION_ID + String.format("%s_%s", this.getId(), activeNode.getId()));
            arrow.setClassifierId(getClassifierId());
            activeNode.addIncomingArrow(arrow);
            addOutgoingArrow(arrow);
            arrow.updateDiff();
        }
    }
}
