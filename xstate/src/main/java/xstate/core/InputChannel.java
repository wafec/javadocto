package xstate.core;

import org.apache.log4j.LogManager;
import org.apache.log4j.Logger;
import xstate.support.Input;

import java.util.ArrayList;

public class InputChannel {
    static Logger log = LogManager.getLogger(InputChannel.class);
    static ArrayList<InputReceiver> inputReceivers = new ArrayList<>();

    InputChannel() {

    }

    public static void broadcastInput(Input input) {
        inputReceivers.stream().forEach(ir -> {
            ir.onReceive(input);
        });
    }

    public static void register(InputReceiver inputReceiver) {
        if (inputReceivers.contains(inputReceiver)) {
            log.warn(String.format("There exist an instance of %s registered in the InputChannel",
                    inputReceiver.toString()));
        }
        inputReceivers.add(inputReceiver);
    }

    public static void unregister(InputReceiver inputReceiver) {
        if (!inputReceivers.contains(inputReceiver)) {
            log.warn(String.format("The instance %s was unregisted before", inputReceiver.toString()));
        }
        inputReceivers.remove(inputReceiver);
    }
}
