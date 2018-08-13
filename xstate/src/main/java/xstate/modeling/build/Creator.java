package xstate.modeling.build;

import org.apache.log4j.Logger;
import xstate.core.Identity;
import xstate.modeling.*;
import xstate.support.*;
import xstate.support.extending.CodeSymbol;

import java.util.ArrayList;
import java.util.HashMap;

public class Creator {
    static Logger log = Logger.getLogger(Creator.class);

    HashMap<String, Node> nodeHashMap = new HashMap<>();
    HashMap<String, Arrow> arrowHashMap = new HashMap<>();
    HashMap<String, Symbol> symbolHashMap = new HashMap<>();
    HashMap<String, Guard> guardHashMap = new HashMap<>();
    HashMap<String, Output> outputHashMap = new HashMap<>();

    String classifierId;

    public Creator() {
        classifierId = "__general_classifier_id__";
    }

    public Creator(String classifierId) {
        this.classifierId = classifierId;
    }

    void createNode(String hash, Node node) {
        if (!nodeHashMap.containsKey(hash)) {
            nodeHashMap.put(hash, node);
            node.setId(hash);
        }
    }

    void createArrow(String hash, Arrow arrow) {
        if (!arrowHashMap.containsKey(hash)) {
            arrowHashMap.put(hash, arrow);
            arrow.setId(hash);
        }
    }

    <T> T cast(HashMap hashMap, String hash, Class<T> clazz) {
        if (hashMap.containsKey(hash)) {
            Object obj = hashMap.get(hash);
            try {
                return (T) obj;
            } catch (ClassCastException exception) {
                return null;
            }
        }
        return null;
    }

    public void createState(String hash, String name) {
        createNode(hash, new State(name));
    }

    public void createRegion(String hash) {
        createNode(hash, new Region());
    }

    public void createTransition(String hash) {
        createArrow(hash, new Transition());
    }

    public void createFirstState(String hash) {
        createNode(hash, new FirstState());
    }

    public void createChoice(String hash) {
        createNode(hash, new Choice());
    }

    public void putStateOnRegion(String regionHash, String stateHash) {
        Region region = cast(nodeHashMap, regionHash, Region.class);
        State state = cast(nodeHashMap, stateHash, State.class);
        if (region != null && state != null) {
            state.clearParent();
            region.addState(state);
        }
    }

    public void putChoiceOnRegion(String regionHash, String choiceHash) {
        Region region = cast(nodeHashMap, regionHash, Region.class);
        Choice choice = cast(nodeHashMap, choiceHash, Choice.class);
        if (region != null && choice != null) {
            choice.clearParent();
            region.addChoice(choice);
        }
    }

    public void putFirstStateOnRegion(String regionHash, String firstStateHash) {
        Region region = cast(nodeHashMap, regionHash, Region.class);
        FirstState firstState = cast(nodeHashMap, firstStateHash, FirstState.class);
        if (region != null & firstState != null) {
            firstState.clearParent();
            region.setFirstState(firstState);
        }
    }

    public void putSubRegionOnState(String stateHash, String subRegionHash) {
        Region region = cast(nodeHashMap, subRegionHash, Region.class);
        State state = cast(nodeHashMap, stateHash, State.class);
        if (region != null && state != null) {
            region.clearParent();
            state.addSubRegion(region);
        }
    }

    public void putTransitionBetweenNodes(String transitionHash, String nodeSourceHash, String nodeDestinationHash) {
        Transition transition = cast(arrowHashMap, transitionHash, Transition.class);
        Node source, destination;
        source = cast(nodeHashMap, nodeSourceHash, Node.class);
        destination = cast(nodeHashMap, nodeDestinationHash, Node.class);
        if (transition != null && source != null && destination != null) {
            if (transition.getSource() != null)
                transition.getSource().removeOutgoingArrow(transition);
            if (transition.getDestination() != null)
                transition.getDestination().removeIncomingArrow(transition);
            source.addOutgoingArrow(transition);
            destination.addIncomingArrow(transition);
            transition.setSource(source);
            transition.setDestination(destination);
            transition.updateDiff();
        }
    }

    void createSymbol(String hash, Symbol symbol) {
        if (!symbolHashMap.containsKey(hash)) {
            symbolHashMap.put(hash, symbol);
        }
    }

    void createGuard(String hash, Guard guard) {
        if (!guardHashMap.containsKey(hash)) {
            guardHashMap.put(hash, guard);
        }
    }

    public void createCodeSymbol(String hash, int number) {
        createSymbol(hash, new CodeSymbol(number));
    }

    public void putSymbolOnTransition(String transitionHash, String symbolHash) {
        Symbol symbol = cast(this.symbolHashMap, symbolHash, Symbol.class);
        Transition transition = cast(arrowHashMap, transitionHash, Transition.class);
        if (symbol != null && transition != null) {
            transition.addSymbol(symbol);
        }
    }

    public void recordGuard(String hash, Guard guard) {
        createGuard(hash, guard);
    }

    public void putGuardOnTransition(String transitionHash, String guardHash) {
        Guard guard = cast(this.guardHashMap, guardHash, Guard.class);
        Transition transition = cast(arrowHashMap, transitionHash, Transition.class);
        if (guard != null && transition != null) {
            transition.addGuard(guard);
        }
    }

    void createOutput(String hash, Output output) {
        if (!outputHashMap.containsKey(hash)) {
            outputHashMap.put(hash, output);
        }
    }

    public void recordOutput(String hash, Output output) {
        createOutput(hash, output);
    }

    public void putOutputOnTransition(String transitionHash, String outputHash) {
        Transition transition = cast(arrowHashMap, transitionHash, Transition.class);
        Output output = cast(this.outputHashMap, outputHash, Output.class);
        if (transition != null && output != null) {
            transition.addOutput(output);
        }
    }

    public void putOutputOnStateForEntering(String stateHash, String outputHash) {
        State state = cast(nodeHashMap, stateHash, State.class);
        Output output = cast(this.outputHashMap, outputHash, Output.class);
        if (state != null && output != null) {
            state.addEntry(output);
        }
    }

    public void putSubmachineOnState(String stateHash, State submachine) {
        String prefix = stateHash + "_" + submachine.getId();
        createRegion( prefix + "_R");
        createFirstState(prefix + "_F");
        putFirstStateOnRegion(prefix + "_R", prefix + "_F");
        putSubRegionOnState(stateHash, prefix + "_R");
        nodeHashMap.put(submachine.getId(), submachine);
        putStateOnRegion(prefix + "_R", submachine.getId());
        createTransition(prefix + "_T");
        putTransitionBetweenNodes(prefix + "_T", prefix + "_F", submachine.getId());
    }

    public void putOutputOnStateForExiting(String stateHash, String outputHash) {
        State state = cast(nodeHashMap, stateHash, State.class);
        Output output = cast(outputHashMap, outputHash, Output.class);
        if (state != null && output != null) {
            state.addExit(output);
        }
    }

    public Node getNode(String hash) {
        return cast(nodeHashMap, hash, Node.class);
    }

    public Symbol getSymbol(String hash) {
        return cast(symbolHashMap, hash, Symbol.class);
    }

    public void setClassifierId(String classifierId) {
        getAllIdentities().forEach(i -> i.setClassifierId(classifierId));
    }

    ArrayList<Identity> getAllIdentities() {
        ArrayList<Identity> identities = new ArrayList<>();

        identities.addAll(nodeHashMap.values());
        identities.addAll(arrowHashMap.values());
        identities.addAll(guardHashMap.values());
        identities.addAll(outputHashMap.values());

        return identities;
    }
}
