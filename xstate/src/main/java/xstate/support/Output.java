package xstate.support;

import xstate.core.Identity;
import xstate.messaging.MessageBroker;
import xstate.support.messaging.OutputMessage;

public class Output extends Identity {
    public void run(Input input) {

    }

    public void message(String descriptor, String... args) {
        MessageBroker.getSingleton().route(OutputMessage.create(this, descriptor, args));
    }
}
