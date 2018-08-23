package xstate.modeling;

import xstate.support.Node;

public class ShallowHistory extends FirstState {
    Node lastActiveNode;

    public void setLastActiveNode(Node lastActiveNode) {
        this.lastActiveNode = lastActiveNode;
    }
}
