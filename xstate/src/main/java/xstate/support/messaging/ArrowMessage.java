package xstate.support.messaging;

import xstate.messaging.Message;
import xstate.support.Arrow;
import xstate.support.Input;

public class ArrowMessage extends Message<Arrow> {
    States state;
    Input incomingInput;

    public static ArrowMessage create(Arrow sender, Input incomingInput, States state) {
        ArrowMessage message = new ArrowMessage();
        message.sender = sender;
        message.state = state;
        message.incomingInput = incomingInput;
        return message;
    }

    public States getState() {
        return state;
    }

    public Input getIncomingInput() {
        return incomingInput;
    }

    @Override
    public String toString() {
        Arrow sender = (Arrow) this.sender;
        return String.format("For input %s, it has %s in %s",
                incomingInput.toString(),
                state.name(),
                sender.getId()
                );
    }

    public enum States {
        TRANSITED,
        SYMBOL_ACCEPTED,
        GUARD_EVALUATED_TO_TRUE,
        GUARD_EVALUATED_TO_FALSE,
        SYMBOL_NOT_ACCEPTED
    }
}
