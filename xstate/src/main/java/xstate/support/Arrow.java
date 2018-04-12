package xstate.support;

import java.util.ArrayList;
import java.util.Collections;

public class Arrow {
    String id;
    Node source, destination;
    ArrayList<Symbol> symbols = new ArrayList<>();
    ArrayList<Guard> guards = new ArrayList<>();
    ArrayList<Output> outputs = new ArrayList<>();
    ArrayList<Node> diffSourcePathForExiting, diffDestinationPathForEntering;
    States state = States.WAITING_INPUT;

    public void setSource(Node source) {
        this.source = source;
    }

    public void setDestination(Node destination) {
        this.destination = destination;
    }

    public void updateDiff() {
        diffSourcePathForExiting = source.getDiffPathNode(destination);
        Collections.reverse(diffSourcePathForExiting);
        diffDestinationPathForEntering = destination.getDiffPathNode(source);
        // need for transition with same source and destination
        // their paths are always the same, therefore producing empty lists
        // source and destination must be always present in both lists
        if (!diffSourcePathForExiting.contains(source)) {
            diffSourcePathForExiting.add(0, source);
        }
        if (!diffDestinationPathForEntering.contains(destination)) {
            diffDestinationPathForEntering.add(destination);
        }
    }

    public void addSymbol(Symbol symbol) {
        if (!symbols.contains(symbol)) {
            symbols.add(symbol);
        }
    }

    public void addGuard(Guard guard) {
        if (!guards.contains(guard)) {
            guards.add(guard);
        }
    }

    public void addOutput(Output output) {
        if (!outputs.contains(output)) {
            outputs.add(output);
        }
    }

    public boolean transit(Input input) {
        state = States.IN_TRANSIT;
        boolean res = inTransit(input);
        state = States.WAITING_INPUT;
        return res;
    }

    boolean inTransit(Input input) {
        if ((symbols.isEmpty() || symbols.stream().anyMatch(s -> s.matchOther(input.getSymbol()))) &&
                (guards.isEmpty() || guards.stream().allMatch(g -> g.eval(input)))) {
            outputs.stream().forEach(o -> o.run(input));
            if (destination.onTransit(input, this)) {
                diffSourcePathForExiting.stream().forEach(n -> n.onExiting(input));
                diffDestinationPathForEntering.subList(0, diffDestinationPathForEntering.size() - 1)
                        .stream().forEach(n -> n.onEntering(input, false));
                diffDestinationPathForEntering.get(diffDestinationPathForEntering.size() - 1).onEntering(input, true);
                diffDestinationPathForEntering.stream().forEach(n -> n.onEntering(input, true));
                return true;
            } else {
                return false;
            }
        }
        return false;
    }

    public States getState() {
        return state;
    }

    public enum States {
        IN_TRANSIT,
        WAITING_INPUT
    }

    public Node getSource() {
        return source;
    }

    public Node getDestination() {
        return destination;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getId() {
        return id;
    }
}
