package statemutest.testcase;

import com.esotericsoftware.yamlbeans.YamlException;
import com.esotericsoftware.yamlbeans.YamlReader;
import com.google.common.collect.Sets;
import geo.algorithm.BinaryInteger;
import geo.algorithm.Objective;
import geo.algorithm.Sequence;
import org.apache.log4j.Logger;
import statemutest.modeling.StateClasses;
import xstate.core.Identity;
import xstate.core.InputReceiver;
import xstate.messaging.Message;
import xstate.messaging.MessageBroker;
import xstate.messaging.Subscriber;
import xstate.messaging.Subscription;
import xstate.modeling.ShallowHistory;
import xstate.modeling.State;
import xstate.modeling.Transition;
import xstate.modeling.messaging.StateMessage;
import xstate.support.*;
import xstate.support.extending.CodeSymbol;
import xstate.support.messaging.ArrowMessage;
import xstate.support.messaging.GuardMessage;

import java.io.*;
import java.lang.reflect.Field;
import java.net.URL;
import java.net.URLClassLoader;
import java.util.*;
import java.util.stream.Stream;

public class GenericGeoTestCaseGenerator implements Subscriber {
    static Logger log = Logger.getLogger(GenericGeoTestCaseGenerator.class);
    ArrayList<String> inputs = new ArrayList<>();
    String testClass;
    File jarFile;
    boolean loaded = false;
    HashMap<String, Integer> stateInputHashMap = new HashMap<>();
    StateInputMapping[] stateInputMappings;
    UserDefinedStateInputMapping[] userDefinedStateInputMappings;
    ArrayList<String> stateIdentities;
    int inputSize;
    int eventsOffset;
    BinaryInteger.Domain defaultSearchDomain = new BinaryInteger.Domain(0, 1000);
    Subscription subscription = new Subscription();
    ArrayList<String> coverageTransitionSet;
    String currentStateIdentity = "";
    int currentStateUserCode = -1;
    int currentBranchDistance;
    ArrayList<String> exercisedTransitionBuffer = new ArrayList<>();
    Set<String> exercisedTransitionSet = new HashSet<>();
    HashMap<String, Integer> arrowAndBranchDistanceMap = new HashMap<>();
    Set<String> coverageTransitionHashSet;
    File instanceSpecification;
    Expected currentExpected;
    StateClasses stateClasses;

    GenericGeoTestCaseGenerator(File jarFile, String testClass, File instanceSpecification, ArrayList<String> inputs, ArrayList<String> stateIdentities) {
        this.jarFile = jarFile;
        this.testClass = testClass;
        this.inputs = inputs;
        this.stateIdentities = stateIdentities;
        this.instanceSpecification = instanceSpecification;
        loadClasses();
        loadMappings();
        subscription.subscriber = this;
        loaded = true;
        subscription.filter = (m) -> {
            Object sender = m.getSender();
            if (sender instanceof Identity) {
                String classifierId = ((Identity) sender).getClassifierId();
                return classifierId.equals("__general_classifier_id__") || classifierId.equals(testClass);
            }
            return true;
        };
    }

    final void loadClasses() {
        stateClasses = new StateClasses(jarFile, testClass, instanceSpecification, inputs, stateIdentities);
    }

    final void loadMappings() {
        stateInputMappings = new StateInputMapping[1 + stateIdentities.size()];
        int stateIndex = 0;
        stateIdentities.add(0, "__default__");
        for (String stateIdentity : stateIdentities) {
            StateInputMapping stateInputMapping = new StateInputMapping();
            stateInputMapping.stateIdentity = stateIdentity;
            stateInputMapping.inputMappings = new InputClassMapping[stateClasses.getLoadedInputs().size()];
            for (int i = 0; i < stateClasses.getLoadedInputs().size(); i++) {
                InputClassMapping inputClassMapping = new InputClassMapping();
                // testId is the input index
                inputClassMapping.testId = i;
                inputClassMapping.loadedInput = stateClasses.getLoadedInputs().get(i);
                inputClassMapping.fields = inputClassMapping.loadedInput.getFields();
                inputClassMapping.initializeFieldDomainAsDefault();
                stateInputMapping.inputMappings[i] = inputClassMapping;
            }
            stateInputMappings[stateIndex] = stateInputMapping;
            stateInputHashMap.put(stateIdentity, stateIndex);
            stateIndex += 1;
        }

        int offset = 0;
        for (StateInputMapping stateInputMapping : stateInputMappings) {
            stateInputMapping.offset = offset;
            for (InputClassMapping inputClassMapping : stateInputMapping.inputMappings) {
                inputClassMapping.offset = offset - stateInputMapping.offset;
                offset += inputClassMapping.fields.length;
            }
        }
        inputSize = offset;
        log.debug("States and input mappings realized");
    }

    protected boolean isLoaded() {
        return loaded;
    }

    public void setStateInputSearchDomain(String state, int testId, String fieldName, int lower, int upper) {
        if (stateInputHashMap.containsKey(state)) {
            int stateInputIndex = stateInputHashMap.get(state);
            StateInputMapping stateInputMapping = stateInputMappings[stateInputIndex];
            if (testId >= 0 && testId < stateInputMapping.inputMappings.length) {
                InputClassMapping inputClassMapping = stateInputMapping.inputMappings[testId];
                int fieldIndex = inputClassMapping.getFieldIndexByName(fieldName);
                if (fieldIndex != -1) {
                    inputClassMapping.fieldSearchDomain[fieldIndex] = new BinaryInteger.Domain(lower, upper);
                    log.debug("Search domain for state " + state + " and field " + fieldName + " redefined to l=" + lower + ", u=" + upper);
                } else {
                    log.error("Field name " + fieldName + " not found");
                }
            } else {
                log.error("Outside bounds for testId of " + testId);
            }
        } else {
            log.error("The hash " + state + " does not exist");
        }
    }

    public int calculateSizeBeforeEventsOffset() {
        int counting = 0;

        for (StateInputMapping stateInputMapping : stateInputMappings) {
            for (InputClassMapping inputClassMapping : stateInputMapping.inputMappings) {
                counting += inputClassMapping.fields.length;
            }
        }

        return counting;
    }

    protected BinaryInteger.Domain[] getSearchDomain(int maxEvents) {
        ArrayList<BinaryInteger.Domain> searchDomain = new ArrayList<>();
        for (StateInputMapping stateInputMapping : stateInputMappings) {
            for (InputClassMapping inputClassMapping : stateInputMapping.inputMappings) {
                int searchDomainIndex = 0;
                for (BinaryInteger.Domain fieldSearchDomain : inputClassMapping.fieldSearchDomain) {
                    BinaryInteger.Domain usedSearchDomain = fieldSearchDomain.clone();
                    if (userDefinedStateInputMappings != null) {
                        final Field field = inputClassMapping.fields[searchDomainIndex];
                        Stream<UserDefinedStateInputMapping> stream = Arrays.asList(userDefinedStateInputMappings).stream().filter(ud -> {
                            return ud.stateIdentity.equals(stateInputMapping.stateIdentity)
                                    && ud.inputClassQualifiedName.equals(inputClassMapping.loadedInput.getCanonicalName())
                                    && ud.fieldName.equals(field.getName());
                        });
                        Optional<UserDefinedStateInputMapping> optional = stream.findFirst();
                        if (optional.isPresent()) {
                            UserDefinedStateInputMapping userDefinedStateInputMapping = optional.get();
                            usedSearchDomain = new BinaryInteger.Domain(userDefinedStateInputMapping.lowerBound, userDefinedStateInputMapping.upperBound);
                            log.debug("States input {" + userDefinedStateInputMapping.stateIdentity + ", " +
                                userDefinedStateInputMapping.inputClassQualifiedName + ", " + userDefinedStateInputMapping.fieldName + "} has changed to " +
                                "lowerBound=" + userDefinedStateInputMapping.lowerBound + " and upperBound=" + userDefinedStateInputMapping.upperBound);
                        }
                    }
                    searchDomain.add(usedSearchDomain);
                    searchDomainIndex += 1;
                }
            }
        }
        eventsOffset = searchDomain.size();
        BinaryInteger.Domain eventsDomain = new BinaryInteger.Domain(0, inputs.size() - 1);
        for (int i = 0; i < maxEvents; i++) {
            searchDomain.add(eventsDomain);
        }
        return searchDomain.toArray(new BinaryInteger.Domain[searchDomain.size()]);
    }

    public void setUserDefinedStateInputMappings(UserDefinedStateInputMapping[] userDefinedStateInputMappings) {
        this.userDefinedStateInputMappings = userDefinedStateInputMappings;
        if (this.userDefinedStateInputMappings == null)
            log.warn("User defined state input mappings was set to NULL");
        else
            log.info(this.userDefinedStateInputMappings.length + " entries set to user defined input mappings");
    }

    protected int getEventsOffset() {
        return eventsOffset;
    }

    protected class InputClassMapping {
        int testId;
        Class loadedInput;
        Field[] fields;
        int offset;
        BinaryInteger.Domain[] fieldSearchDomain;

        void initializeFieldDomainAsDefault() {
            fieldSearchDomain = new BinaryInteger.Domain[fields.length];
            for (int i = 0; i < fieldSearchDomain.length; i++) {
                fieldSearchDomain[i] = defaultSearchDomain;
            }
        }

        int getFieldIndexByName(String name) {
            for (int i = 0; i < fields.length; i++) {
                if (fields[i].getName().equals(name)) {
                    return i;
                }
            }
            return -1;
        }
    }

    protected class StateInputMapping {
        int offset;
        String stateIdentity;
        InputClassMapping[] inputMappings;
    }

    public static class UserDefinedStateInputMapping {
        public String stateIdentity;
        public String inputClassQualifiedName;
        public String fieldName;
        public int lowerBound;
        public int upperBound;

        public UserDefinedStateInputMapping clone() {
            UserDefinedStateInputMapping newInstance = new UserDefinedStateInputMapping();
            newInstance.stateIdentity = stateIdentity;
            newInstance.inputClassQualifiedName = inputClassQualifiedName;
            newInstance.fieldName = fieldName;
            newInstance.lowerBound = lowerBound;
            newInstance.upperBound = upperBound;
            return newInstance;
        }

        boolean isStrEqual(String a, String b) {
            if (a == null && b != null)
                return false;
            if (a != null && b == null)
                return false;
            if (a == null && b == null)
                return true;
            return a.equals(b);
        }

        public boolean isParamsEqual(UserDefinedStateInputMapping other) {
            if (other == null)
                return false;
            return isStrEqual(stateIdentity, other.stateIdentity) &&
                    isStrEqual(inputClassQualifiedName, other.inputClassQualifiedName) &&
                    isStrEqual(fieldName, other.fieldName);
        }
    }

    protected Input getInput(int testId, Sequence sequence) {
        if (currentStateUserCode != -1) {
            return getInput(currentStateUserCode, testId, sequence);
        }
        return getInput(currentStateIdentity, testId, sequence);
    }

    protected Input getInput(String stateIdentity, int testId, Sequence sequence) {
        int stateInputIndex = 0;
        if (stateInputHashMap.containsKey(stateIdentity)) {
            stateInputIndex = stateInputHashMap.get(stateIdentity);
        }
        return getInput(stateInputIndex, testId, sequence);
    }

    protected Input getInput(int stateInputIndex, int testId, Sequence sequence) {
        StateInputMapping stateInputMapping = stateInputMappings[stateInputIndex];
        InputClassMapping inputClassMapping = stateInputMapping.inputMappings[testId];
        int offset = stateInputMapping.offset + inputClassMapping.offset;
        Args args = new Args(inputClassMapping.fields.length);
        for (int i = 0; i < args.getSize(); i++) {
            BinaryInteger.Domain domain = inputClassMapping.fieldSearchDomain[i];
            // lower and upper might be positive
            args.set(i, sequence.getProjectVariables()[offset + i].getValue());
        }
        Input newInput = new Input(new CodeSymbol(inputClassMapping.loadedInput.hashCode()), args);
        return newInput;
    }

    protected void sendInput(InputReceiver testClassInstance, Input input) {
        // using interface there is no need to use reflection
        testClassInstance.onReceive(input);
    }

    // This method is very import in this class
    // Here we obtain all results from the model execution
    public void accept(Message message) {
        if (message instanceof ArrowMessage) {
            ArrowMessage arrowMessage = (ArrowMessage) message;
            Arrow sender = arrowMessage.getSender();
            if (arrowMessage.getState() == ArrowMessage.States.TRANSITED) {
                exercisedTransitionBuffer.add(sender.getId());
                exercisedTransitionSet.add(sender.getId());
                currentBranchDistance = Integer.MAX_VALUE;
                // transition result for test generation
                addResultIfNonNull(new GoodTransitionResult(arrowMessage.getSender()));
            }
        } else if (message instanceof StateMessage) {
            StateMessage stateMessage = (StateMessage) message;
            State sender = stateMessage.getSender();
            if (stateMessage.getStateOfState() == StateMessage.States.ENTERED) {
                currentStateIdentity = sender.getId();
                if (sender.getUserCode() == -1) {
                    if (stateInputHashMap.containsKey(currentStateIdentity)) {
                        sender.setUserCode(stateInputHashMap.get(currentStateIdentity));
                    } else {
                        sender.setUserCode(0);
                    }
                }
                currentStateUserCode = sender.getUserCode();
            }
        } else if (message instanceof GuardMessage) {
            GuardMessage guardMessage = (GuardMessage) message;
            currentBranchDistance = Math.min(currentBranchDistance, guardMessage.getDistance());

            // to test case generation be faster
            Guard sender = guardMessage.getSender();
            if (sender.getArrow() != null) {
                if (!arrowAndBranchDistanceMap.containsKey(sender.getArrow().getId())) {
                    arrowAndBranchDistanceMap.put(sender.getArrow().getId(), guardMessage.getDistance());
                } else {
                    int currentBranchDistance = arrowAndBranchDistanceMap.get(sender.getArrow().getId());
                    if (currentBranchDistance > guardMessage.getDistance()) {
                        arrowAndBranchDistanceMap.put(sender.getArrow().getId(), guardMessage.getDistance());
                    }
                }
            }
        }
    }

    protected void addResultIfNonNull(AbstractResult result) {
        if (currentExpected != null) {
            currentExpected.addResult(result);
        }
    }

    protected void setupTestCaseGeneration(ArrayList<String> coverageTransitionSet) {
        MessageBroker.getSingleton().addSubscription(subscription);
        this.coverageTransitionSet = coverageTransitionSet;
        this.coverageTransitionHashSet = new HashSet<>(this.coverageTransitionSet);
    }

    protected void cleanUpTestCaseGeneration() {
        MessageBroker.getSingleton().removeSubscriber(this);
    }

    protected ArrayList<Input> evaluateTestClassInstance(Sequence sequence) {
        return evaluateTestClassInstance(stateClasses.createTestClassInstance(), sequence);
    }

    protected ArrayList<Input> evaluateTestClassInstance(InputReceiver testClassInstance, Sequence sequence) {
        exercisedTransitionBuffer.clear();
        exercisedTransitionSet.clear();
        arrowAndBranchDistanceMap.clear();
        currentBranchDistance = Integer.MAX_VALUE;
        ArrayList<Input> usedInputs = new ArrayList<>();
        // bug: last execution produce a noise of first initialization
        // fix: assign nil to currentExpected
        // impact: first transition from initial to destination will not be captured
        currentExpected = null;
        for (int i = getEventsOffset(); i < sequence.getProjectVariables().length; i++) {
            //log.debug("event=" + i + ", sequence=" + sequence.getProjectVariables()[i].getValue());
            Input input = getInput(sequence.getProjectVariables()[i].getValue(), sequence);
            currentExpected = new Expected(input);
            usedInputs.add(currentExpected);
            sendInput(testClassInstance, currentExpected);
            new InnoportuneResult().insertIfNeeded(currentExpected.results);
        }
        currentExpected = null;

        return usedInputs;
    }

    protected ArrayList generateObjectDataSet(ArrayList<Input> inputDataSet) {
        ArrayList objectDataSet = new ArrayList();
        for (Input input : inputDataSet) {
            for (Class loadedInput : stateClasses.getLoadedInputs()) {
                CodeSymbol codeSymbol = (CodeSymbol) input.getSymbol();
                if (loadedInput.hashCode() == codeSymbol.getNumber()) {
                    objectDataSet.add(Input.createFrom(input, loadedInput));
                    break;
                }
            }
        }
        return objectDataSet;
    }

    class GenericTestObjective implements Objective {
        int k = 1000;

        @Override
        public double eval(Object object) {
            Sequence sequence = (Sequence) object;
            evaluateTestClassInstance(sequence);
            int difference = Sets.difference(coverageTransitionHashSet, exercisedTransitionSet).size();
            int branchDistance = currentBranchDistance;

            // this maximizes the chance to trace the right path when it is a sequence
            // arrowAndBranchDistanceMap
            if (arrowAndBranchDistanceMap.size() > 0) {
                Sets.SetView<String> view = Sets.intersection(coverageTransitionHashSet, arrowAndBranchDistanceMap.keySet());
                if (view.size() > 0) {
                    int newBranchDistance = Integer.MAX_VALUE;
                    for (String key : view) {
                        int candidateBranchDistance = arrowAndBranchDistanceMap.get(key);
                        if (candidateBranchDistance > 0)
                            newBranchDistance = Math.min(newBranchDistance, candidateBranchDistance);
                    }
                    if (branchDistance != Integer.MAX_VALUE) {
                        branchDistance = newBranchDistance;
                    }
                }
            }

            double value = difference;
            if (value > 0) {
                value = value * k;
                value += k - 1;
                value -= (k - 1) - branchDistance;
            }
            return value;
        }
    }

    public class Expected extends Input {
        private List<AbstractResult> results;

        public Expected(Symbol symbol, Args args) {
            super(symbol, args);
            results = new ArrayList<>();
        }

        public Expected(Input input) {
            this(input.getSymbol(), input.getArgs());
        }

        public void addResult(AbstractResult result) {
            if (!results.contains(result)) {
                results.add(result);
            }
        }

        public void removeResult(AbstractResult result) {
            if (results.contains(result)) {
                results.remove(result);
            }
        }

        public List<AbstractResult> getResults() {
            return new ArrayList<>(results);
        }
    }

    public abstract class AbstractResult {

    }

    public class InnoportuneResult extends AbstractResult {
        InnoportuneResult() {

        }

        public void insertIfNeeded(List<AbstractResult> results) {
            if (results.stream().noneMatch(r -> r instanceof GoodTransitionResult)) {
                results.add(new InnoportuneResult());
            }
        }
    }

    public class GoodTransitionResult extends AbstractResult {
        public String transition;
        public String source;
        public String destination;

        public GoodTransitionResult() {

        }

        protected GoodTransitionResult(Arrow arrow) {
            transition = arrow.getId();
            if (arrow.getSource() != null)
                source = arrow.getSource().getId();
            if (arrow.getDestination() != null)
                destination = arrow.getDestination().getId();
        }
    }
}
