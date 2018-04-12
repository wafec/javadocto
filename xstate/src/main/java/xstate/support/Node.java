package xstate.support;

import java.util.ArrayList;
import java.util.Collections;
import java.util.stream.Collectors;

public class Node {
    Node parent;
    ArrayList<Node> children = new ArrayList<>();
    ArrayList<Node> startingNodes = new ArrayList<>();
    protected ArrayList<Arrow> outgoingArrows = new ArrayList<>();
    protected ArrayList<Arrow> incomingArrows = new ArrayList<>();
    protected boolean active = false;

    public ArrayList<Node> getPath() {
        ArrayList<Node> path = new ArrayList<>();
        path.add(this);
        Node nonNull = parent;
        while (nonNull != null) {
            path.add(nonNull);
            nonNull = nonNull.parent;
        }
        Collections.reverse(path);
        return path;
    }

    public ArrayList<Node> getCommonPathNode(Node fromOther) {
        ArrayList<Node> pathOne, pathOther;
        pathOne = this.getPath();
        pathOther = fromOther.getPath();
        Node compOne, compOther;
        ArrayList<Node> commonPathNode = new ArrayList<>();
        for (int i = 0; i < Math.min(pathOne.size(), pathOther.size()); i++) {
            compOne = pathOne.get(i);
            compOther = pathOther.get(i);
            if (compOne == compOther)
                commonPathNode.add(compOne);
            else
                break;
        }
        return commonPathNode;
    }

    public ArrayList<Node> getDiffPathNode(Node fromOther) {
        ArrayList<Node> commonPathNode = getCommonPathNode(fromOther);
        ArrayList<Node> myPath = this.getPath();
        ArrayList<Node> diffPathNode = new ArrayList<>();
        for (int i = commonPathNode.size(); i < myPath.size(); i++) {
            diffPathNode.add(myPath.get(i));
        }
        return diffPathNode;
    }

    public boolean isActive() {
        return active;
    }

    public boolean onTransit(Input input, Arrow from) {
        return true;
    }

    public void onExiting(Input input) {
        if (active) {
            children.stream().filter(c -> c.isActive()).forEach(c -> c.onExiting(input));
            onExit(input);
            active = false;
        }
    }

    protected void onExit(Input input) {

    }

    public void onEntering(Input input, boolean inDepth) {
        if (!active) {
            onEntry(input);
            active = true;
            if (inDepth) {
                startingNodes.stream().filter(c -> !c.isActive()).forEach(c -> c.onEntering(input, true));
            }
        }
    }

    public void onEntering(boolean inDepth) {
        onEntering(null, inDepth);
    }

    public void onEntering() {
        onEntering(true);
    }

    protected void onEntry(Input input) {

    }

    public boolean onInput(Input input) {
        if (active) {
            // when backing it is possible a non active be active
            // complexity remains same doing so
            children.stream().filter(c -> c.isActive())
                    .collect(Collectors.toList())
                    .forEach(c -> c.onInput(input));
            boolean hasTransited = false;
            for (Arrow arrow : outgoingArrows) {
                hasTransited = arrow.transit(input) || hasTransited;
            }
            return hasTransited;
        }
        return false;
    }

    public void addChild(Node child) {
        if (!children.contains(child)) {
            children.add(child);
            child.setParent(this);
        }
    }

    public void setParent(Node parent) {
        this.parent = parent;
    }

    public void addStartingNode(Node startingNode) {
        if (!startingNodes.contains(startingNode)) {
            startingNodes.add(startingNode);
            startingNode.setParent(this);
        }
    }

    public void addOutgoingArrow(Arrow arrow) {
        if (!outgoingArrows.contains(arrow)) {
            outgoingArrows.add(arrow);
        }
    }

    public void addIncomingArrow(Arrow arrow) {
        if (!incomingArrows.contains(arrow)) {
            incomingArrows.add(arrow);
        }
    }

    public void setJustOneStartingNode(Node startingNode) {
        startingNodes.stream().forEach(s -> s.setParent(null));
        startingNodes.clear();
        addStartingNode(startingNode);
    }

    public void clearParent() {
        if (parent != null) {
            parent.children.remove(this);
            parent = null;
        }
    }

    public void removeIncomingArrow(Arrow arrow) {
        if (incomingArrows.contains(arrow)) {
            incomingArrows.remove(arrow);
        }
    }

    public void removeOutgoingArrow(Arrow arrow) {
        if (outgoingArrows.contains(arrow)) {
            outgoingArrows.remove(arrow);
        }
    }
}
