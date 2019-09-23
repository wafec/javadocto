package statemutest.application;

import org.apache.commons.cli.*;
import org.apache.commons.io.FileUtils;
import org.apache.log4j.LogManager;
import org.apache.log4j.Logger;
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
    private static final Logger log = LogManager.getLogger(TestCaseAnimation.class);
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
        System.out.println(String.format("Target is %s", _targetQualifiedName));
        try {
            List<String> lines = FileUtils.readLines(new File(_inputsFilepath));
            InputReceiver receiver = _instanceProvider.getReceiver(_targetQualifiedName);
            MessageBroker.getSingleton().addSubscription(createSubscription());
            for (String line : lines) {
                String[] entries = line.split("\\s", -1);
                if (isLineValid(entries)) {
                    System.out.println(String.format("Send \"%s\"", line.replace("\n", "")));
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
            log.error(exc.getMessage(), exc);
        } finally {
            if (_subscription != null) {
                MessageBroker.getSingleton().removeSubscriber(_subscription.subscriber);
            }
        }
    }

    public static void main(String[] args) throws Exception {
        System.out.println("Model animation started!");
        Options opts = new Options();
        Option inputsOpt = new Option("i", "inputs", true, "Inputs filepath");
        inputsOpt.setRequired(true);
        opts.addOption(inputsOpt);
        Option instantiationOpt = new Option("s", "instantiation", true, "Instantiation specification filepath");
        instantiationOpt.setRequired(true);
        opts.addOption(instantiationOpt);
        Option umlOpt = new Option("u", "uml", true, "UML specification filepath");
        umlOpt.setRequired(true);
        opts.addOption(umlOpt);
        Option classpathOpt = new Option("cp", "classpath", true, "Java classpath");
        classpathOpt.setRequired(true);
        opts.addOption(classpathOpt);
        Option targetOpt = new Option("t", "target", true, "Target qualified name");
        targetOpt.setRequired(true);
        opts.addOption(targetOpt);
        CommandLineParser parser = new DefaultParser();
        CommandLine cmd = parser.parse(opts, args);
        String xmiFilepath = cmd.getOptionValue("uml");
        String instantiation = cmd.getOptionValue("instantiation");
        String classpath = cmd.getOptionValue("classpath");
        String inputs = cmd.getOptionValue("inputs");
        String target = cmd.getOptionValue("target");
        InstanceProvider provider = new InstanceProvider(xmiFilepath, instantiation, classpath);
        TestCaseAnimation animation = new TestCaseAnimation(provider, inputs, target);
        animation.run();
    }

    @Override
    public void accept(Message message) {
        System.out.println(message.toString());
    }
}
