package statemutest.meter;

import org.apache.log4j.Logger;
import statemutest.application.GenericSetup;
import statemutest.application.TestCaseObject;
import statemutest.modeling.StateClasses;
import xstate.core.InputReceiver;
import xstate.messaging.Message;
import xstate.messaging.MessageBroker;
import xstate.messaging.Subscriber;
import xstate.messaging.Subscription;
import xstate.modeling.messaging.StateMessage;
import xstate.support.Arrow;
import xstate.support.Input;
import xstate.support.messaging.ArrowMessage;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.stream.Collectors;

public class CoverageMeter implements Subscriber {
    static Logger log = Logger.getLogger(CoverageMeter.class);

    GenericSetup genericSetup;
    ArrayList<TestCaseObject> testCases;
    ArrayList<AbstractCoverage> coverages;
    Subscription subscription;
    protected final ArrayList<Arrow> exercisedArrows = new ArrayList<>();
    protected final ArrayList<Arrow> transientExercisedArrows = new ArrayList<>();
    protected final ArrayList<Input> sentInputs = new ArrayList<>();
    protected final ArrayList<xstate.modeling.State> statesConfiguration = new ArrayList<>();
    protected final HashMap<Input, Class> inputClassMapping = new HashMap<>();

    StateClasses stateClasses;

    public CoverageMeter(GenericSetup genericSetup, ArrayList<TestCaseObject> testCases, ArrayList<AbstractCoverage> coverages) {
        this.genericSetup = genericSetup;
        this.testCases = testCases;
        this.coverages = coverages;
        stateClasses = new StateClasses(genericSetup);
    }

    void iterateCoverageInstances(States state) {
        for (AbstractCoverage coverage : coverages) {
            coverage.accept(state, this);
        }
    }

    public void measure() {
        subscription = new Subscription();
        subscription.subscriber = this;
        MessageBroker.getSingleton().addSubscription(subscription);
        iterateCoverageInstances(States.PRE_MEASURING);
        statesConfiguration.clear();
        inputClassMapping.clear();
        for (int i = 0; i < testCases.size(); i++) {
            TestCaseObject testCase = testCases.get(i);
            List<Input> inputs = (List<Input>) testCase.inputSet.stream().map(inp -> {
                Class inputClass = stateClasses.getInputClassByQualifiedName(inp.qualifiedName);
                Object instance = stateClasses.createInputInstanceFromMap(inp.args, inputClass);
                Input input = Input.createTo(instance, inputClass);
                inputClassMapping.put(input, inputClass);
                return input;
            }).collect(Collectors.toList());
            ArrayList<Input> inputDataSet = new ArrayList<>(inputs);
            exercisedArrows.clear();
            iterateCoverageInstances(States.PRE_EXECUTION);
            InputReceiver testClassInstance = createTestClassInstance();
            for (int j = 0; j < inputDataSet.size(); j++) {
                Input input = inputDataSet.get(j);
                sentInputs.clear();
                sentInputs.add(input);
                transientExercisedArrows.clear();
                iterateCoverageInstances(States.BEFORE_EXECUTION);
                testClassInstance.onReceive(input);
                iterateCoverageInstances(States.AFTER_EXECUTION);
            }
            iterateCoverageInstances(States.POST_EXECUTION);
        }
        iterateCoverageInstances(States.POST_MEASURING);
        MessageBroker.getSingleton().removeSubscriber(this);
    }

    InputReceiver createTestClassInstance() {
        return stateClasses.createTestClassInstance();
    }

    public void accept(Message message) {
        if (message instanceof ArrowMessage) {
            ArrowMessage arrowMessage = (ArrowMessage) message;
            if (arrowMessage.getState().equals(ArrowMessage.States.TRANSITED)) {
                exercisedArrows.add(arrowMessage.getSender());
                transientExercisedArrows.add(arrowMessage.getSender());
            }
        } else if (message instanceof StateMessage) {
            StateMessage stateMessage = (StateMessage) message;
            switch (stateMessage.getStateOfState()) {
                case ENTERED:
                    if (!statesConfiguration.contains(stateMessage.getSender())) {
                        statesConfiguration.add(stateMessage.getSender());
                    }
                    break;
                case EXITED:
                    if (statesConfiguration.contains(stateMessage.getSender())) {
                        statesConfiguration.remove(stateMessage.getSender());
                    }
                    break;
            }
        }
    }

    public enum States {
        PRE_EXECUTION,
        POST_EXECUTION,
        PRE_MEASURING,
        POST_MEASURING,
        BEFORE_EXECUTION,
        AFTER_EXECUTION
    }
}
