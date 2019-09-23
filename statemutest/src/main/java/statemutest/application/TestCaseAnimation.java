package statemutest.application;

import statemutest.util.InstanceProvider;
import xstate.core.InputReceiver;
import xstate.messaging.Message;
import xstate.messaging.MessageBroker;
import xstate.messaging.Subscriber;
import xstate.messaging.Subscription;
import xstate.support.Input;

import java.io.File;
import java.nio.file.Files;
import java.util.List;

public class TestCaseAnimation implements Subscriber {
    private String _inputsFilepath;
    private InstanceProvider _instanceProvider;
    private String _targetQualifiedName;
    private Subscription _subscription;
    private static final int EVENT_INDEX = 0;
    private static final int FIELD_INDEX = 0;
    private static final int VALUE_INDEX = 1;

    private TestCaseAnimation(InstanceProvider instanceProvider, String inputsFilepath, String targetQualifiedName) {
        this._inputsFilepath = inputsFilepath;
        this._instanceProvider = instanceProvider;
        this._targetQualifiedName = targetQualifiedName;
        run();
    }

    public boolean isLineValid(String[] entries) {
        if (entries == null || entries.length == 0)
            return false;
        if (entries.length % 2 == 0)
            return false;
        return true;
    }

    private Subscription createSubscription() {
        _subscription = new Subscription();
        _subscription.subscriber = this;
        _subscription.filter = (m) -> {
            return true;
        };
        return _subscription;
    }

    public void run() {
        try {
            List<String> lines = Files.readAllLines(new File(_inputsFilepath).toPath());
            InputReceiver receiver = _instanceProvider.getReceiver(_targetQualifiedName);
            MessageBroker.getSingleton().addSubscription(createSubscription());
            for (String line : lines) {
                String[] entries = line.split("\\s", -1);
                System.out.println(String.format("%d, %s\n", entries.length, line));
                if (isLineValid(entries)) {
                    InstanceProvider.RawInput rawInput = _instanceProvider.getRawInput(entries[EVENT_INDEX]);
                    for (int i = 1; i < entries.length; i += 2) {
                        rawInput.setValue(entries[i + FIELD_INDEX], Integer.valueOf(entries[i  + VALUE_INDEX]));
                    }
                    Input input = rawInput.get();
                    receiver.onReceive(input);
                }
            }
        } catch (Exception exc) {
            System.out.println("It was not possible to run the model, sorry! See logs for more details.");
            exc.printStackTrace();
        } finally {
            if (_subscription != null) {
                MessageBroker.getSingleton().removeSubscriber(_subscription.subscriber);
            }
        }
    }

    public static void main(String[] args) {
        String inputs = "H:\\DATA\\development\\papyrus-workspace\\ATM_MODEL\\animation\\scenario001.inputs.txt";
        String instantiation = "H:\\DATA\\development\\papyrus-workspace\\ATM_MODEL\\animation\\scenario001.instantiation.yaml";
        String xmiFilepath = "H:\\DATA\\development\\papyrus-workspace\\ATM_MODEL\\ATM_MODEL.uml";
        String classpath = "H:\\WINDOWS\\Development\\javadocto\\statemutest\\build\\libs\\statemutest-all-1.0.jar";
        InstanceProvider provider = new InstanceProvider(xmiFilepath, instantiation, classpath);
        TestCaseAnimation animation = new TestCaseAnimation(provider, inputs, "atm.target.Atm");
        animation.run();
    }

    @Override
    public void accept(Message message) {

    }
}
