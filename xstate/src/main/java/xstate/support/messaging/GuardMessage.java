package xstate.support.messaging;

import xstate.messaging.Message;
import xstate.support.Guard;
import xstate.support.Input;

public class GuardMessage extends Message<Guard> {
    int distance;
    Input input;

    public static GuardMessage create(Guard sender, int distance, Input input) {
        GuardMessage message = new GuardMessage();
        message.sender = sender;
        message.distance = distance;
        message.input = input;
        return message;
    }

    public int getDistance() {
        return distance;
    }

    public Input getInput() {
        return input;
    }

    @Override
    public String toString() {
        Guard sender = (Guard) this.sender;
        return String.format("For input %s, distance is %d in %s", input.toString(), distance, sender.getArrow().getId());
    }
}
