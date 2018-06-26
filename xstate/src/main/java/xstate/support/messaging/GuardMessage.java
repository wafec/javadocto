package xstate.support.messaging;

import xstate.messaging.Message;
import xstate.support.Guard;

public class GuardMessage extends Message<Guard> {
    int distance;

    public static GuardMessage create(Guard sender, int distance) {
        GuardMessage message = new GuardMessage();
        message.sender = sender;
        message.distance = distance;
        return message;
    }

    public int getDistance() {
        return distance;
    }
}
