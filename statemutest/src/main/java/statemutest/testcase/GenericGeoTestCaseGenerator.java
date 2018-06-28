package statemutest.testcase;

import com.esotericsoftware.yamlbeans.YamlException;
import com.esotericsoftware.yamlbeans.YamlReader;
import com.google.common.collect.Sets;
import geo.algorithm.BinaryInteger;
import geo.algorithm.Objective;
import geo.algorithm.Sequence;
import org.apache.log4j.Logger;
import xstate.messaging.Message;
import xstate.messaging.MessageBroker;
import xstate.messaging.Subscriber;
import xstate.messaging.Subscription;
import xstate.modeling.State;
import xstate.modeling.messaging.StateMessage;
import xstate.support.Args;
import xstate.support.Arrow;
import xstate.support.Input;
import xstate.support.extending.CodeSymbol;
import xstate.support.messaging.ArrowMessage;
import xstate.support.messaging.GuardMessage;

import java.io.*;
import java.lang.reflect.Field;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.net.URL;
import java.net.URLClassLoader;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Set;

public class GenericGeoTestCaseGenerator implements Subscriber {
    static Logger log = Logger.getLogger(GenericGeoTestCaseGenerator.class);
    ArrayList<String> inputs = new ArrayList<>();
    String testClass;
    File jarFile;
    Class loadedTestClass;
    Method onReceiveMethod;
    ArrayList<Class> loadedInputs;
    URLClassLoader urlClassLoader;
    boolean loaded = false;
    HashMap<String, Integer> stateInputHashMap = new HashMap<>();
    StateInputMapping[] stateInputMappings;
    ArrayList<String> stateIdentities;
    int inputSize;
    int eventsOffset;
    BinaryInteger.Domain defaultSearchDomain = new BinaryInteger.Domain(0, 1000, numberOfBits(0, 1000));
    Subscription subscription = new Subscription();
    ArrayList<String> coverageTransitionSet;
    String currentStateIdentity = "";
    int currentStateUserCode = -1;
    int currentBranchDistance = 0;
    ArrayList<String> exercisedTransitionBuffer = new ArrayList<>();
    Set<String> exercisedTransitionSet = new HashSet<>();
    Set<String> coverageTransitionHashSet;
    File instanceSpecification;
    String instanceSpecificationText;

    GenericGeoTestCaseGenerator(File jarFile, String testClass, File instanceSpecification, ArrayList<String> inputs, ArrayList<String> stateIdentities) {
        this.jarFile = jarFile;
        this.testClass = testClass;
        this.inputs = inputs;
        this.stateIdentities = stateIdentities;
        this.instanceSpecification = instanceSpecification;
        loadClasses();
        loadMappings();
        loadSpecification();
        subscription.subscriber = this;
        loaded = true;
    }

    final void loadClasses() {
        try {
            urlClassLoader = URLClassLoader.newInstance(new URL[] { jarFile.toURI().toURL() });
            loadedTestClass = urlClassLoader.loadClass(testClass);
            loadedInputs = new ArrayList<>();
            for (String input : inputs) {
                loadedInputs.add(urlClassLoader.loadClass(input));
            }
            onReceiveMethod = loadedTestClass.getMethod("onReceive", Input.class);
            log.debug("State machine class and input classes loaded");
        } catch (IOException exception) {
            log.error(exception.getMessage());
        } catch (ClassNotFoundException | NoSuchMethodException exception) {
            log.error(exception.getMessage());
        }
    }

    final void loadMappings() {
        stateInputMappings = new StateInputMapping[1 + stateIdentities.size()];
        int stateIndex = 0;
        stateIdentities.add(0, "__default__");
        for (String stateIdentity : stateIdentities) {
            StateInputMapping stateInputMapping = new StateInputMapping();
            stateInputMapping.stateIdentity = stateIdentity;
            stateInputMapping.inputMappings = new InputClassMapping[loadedInputs.size()];
            for (int i = 0; i < loadedInputs.size(); i++) {
                InputClassMapping inputClassMapping = new InputClassMapping();
                // testId is the input index
                inputClassMapping.testId = i;
                inputClassMapping.loadedInput = loadedInputs.get(i);
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
        log.debug("State and input mappings realized");
    }

    final void loadSpecification() {
        try {
            FileInputStream fileStream = new FileInputStream(this.instanceSpecification);
            byte[] content = new byte[fileStream.available()];
            fileStream.read(content);
            fileStream.close();
            this.instanceSpecificationText = new String(content);
            log.debug("Specification loaded in memory");
        } catch (IOException exception) {
            log.error(exception.getMessage());
        }
    }

    protected boolean isLoaded() {
        return loaded;
    }

    int numberOfBits(int lower, int upper) {
        int inter = Math.abs(lower - upper);
        return (int) (Math.ceil(Math.log(inter) / Math.log(2)));
    }

    public void setStateInputSearchDomain(String state, int testId, String fieldName, int lower, int upper) {
        if (stateInputHashMap.containsKey(state)) {
            int stateInputIndex = stateInputHashMap.get(state);
            StateInputMapping stateInputMapping = stateInputMappings[stateInputIndex];
            if (testId >= 0 && testId < stateInputMapping.inputMappings.length) {
                InputClassMapping inputClassMapping = stateInputMapping.inputMappings[testId];
                int fieldIndex = inputClassMapping.getFieldIndexByName(fieldName);
                if (fieldIndex != -1) {
                    inputClassMapping.fieldSearchDomain[fieldIndex] = new BinaryInteger.Domain(lower, upper, numberOfBits(lower, upper));
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

    protected BinaryInteger.Domain[] getSearchDomain(int maxEvents) {
        ArrayList<BinaryInteger.Domain> searchDomain = new ArrayList<>();
        for (StateInputMapping stateInputMapping : stateInputMappings) {
            for (InputClassMapping inputClassMapping : stateInputMapping.inputMappings) {
                for (BinaryInteger.Domain fieldSearchDomain : inputClassMapping.fieldSearchDomain) {
                    searchDomain.add(fieldSearchDomain);
                }
            }
        }
        eventsOffset = searchDomain.size();
        BinaryInteger.Domain eventsDomain = new BinaryInteger.Domain(0, inputs.size(), numberOfBits(0, inputs.size()));
        for (int i = 0; i < maxEvents; i++) {
            searchDomain.add(eventsDomain);
        }
        return searchDomain.toArray(new BinaryInteger.Domain[searchDomain.size()]);
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
            args.set(i, sequence.getProjectVariables()[offset + i].getValue()
                    + domain.getLowerBound() - (domain.getInterval() / 2));
        }
        Input newInput = new Input(new CodeSymbol(inputClassMapping.loadedInput.hashCode()), args);
        return newInput;
    }

    protected Object createTestClassInstance() {
        try {
            YamlReader reader = new YamlReader(instanceSpecificationText);
            Object testClassInstance = reader.read(loadedTestClass);
            return testClassInstance;
        } catch (YamlException exception) {
            log.error(exception.getMessage());
        }

        return null;
    }

    protected void sendInput(Object testClassInstance, Input input) {
        try {
            onReceiveMethod.invoke(testClassInstance, input);
        } catch (InvocationTargetException | IllegalAccessException exception) {
            log.error(exception.getMessage());
        }
    }

    protected Class getLoadedTestClass() {
        return loadedTestClass;
    }

    public void accept(Message message) {
        if (message instanceof ArrowMessage) {
            ArrowMessage arrowMessage = (ArrowMessage) message;
            Arrow sender = arrowMessage.getSender();
            if (arrowMessage.getState() == ArrowMessage.States.TRANSITED) {
                exercisedTransitionBuffer.add(sender.getId());
                exercisedTransitionSet.add(sender.getId());
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
            currentBranchDistance = Math.max(currentBranchDistance, guardMessage.getDistance());
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
        return evaluateTestClassInstance(createTestClassInstance(), sequence);
    }

    protected ArrayList<Input> evaluateTestClassInstance(Object testClassInstance, Sequence sequence) {
        exercisedTransitionBuffer.clear();
        exercisedTransitionSet.clear();
        ArrayList<Input> usedInputs = new ArrayList<>();

        for (int i = getEventsOffset(); i < sequence.getProjectVariables().length; i++) {
            //log.debug("event=" + i + ", sequence=" + sequence.getProjectVariables()[i].getValue());
            Input input = getInput(sequence.getProjectVariables()[i].getValue(), sequence);
            usedInputs.add(input);
            sendInput(testClassInstance, input);
        }

        return usedInputs;
    }

    protected ArrayList generateObjectDataSet(ArrayList<Input> inputDataSet) {
        ArrayList objectDataSet = new ArrayList();
        for (Input input : inputDataSet) {
            for (Class loadedInput : loadedInputs) {
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
        @Override
        public double eval(Object object) {
            Sequence sequence = (Sequence) object;
            evaluateTestClassInstance(sequence);
            Sets.SetView<String> setView = Sets.difference(coverageTransitionHashSet, exercisedTransitionSet);
            double value = setView.size();
            if (value > 0) {
                double branchScale = 1000000.0;
                double normalizedBranchDistance = currentBranchDistance / branchScale;
                value += normalizedBranchDistance;
            }
            return value;
        }
    }
}
