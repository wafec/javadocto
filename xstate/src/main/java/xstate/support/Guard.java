package xstate.support;

import xstate.messaging.MessageBroker;
import xstate.support.messaging.GuardMessage;

public class Guard {
    public boolean eval(Input input) {
        int distance = evalInteger(input);
        MessageBroker.getSingleton().route(GuardMessage.create(this, distance, input));
        return distance == 0;
    }

    protected int evalInteger(Input input) {
        // 0 - means it is true
        // > 0 means how distance is the condition to be true
        return 0;
    }
}
