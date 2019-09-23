package xstate.modeling.messaging;

import xstate.messaging.Message;
import xstate.modeling.State;

public class StateMessage extends Message<State> {
    States stateOfState;

    public static StateMessage create(State state, States stateOfState) {
        StateMessage stateMessage = new StateMessage();
        stateMessage.sender = state;
        stateMessage.stateOfState = stateOfState;
        return stateMessage;
    }

    public States getStateOfState() {
        return stateOfState;
    }

    @Override
    public String toString() {
        State sender = (State) this.sender;
        return String.format("%s state has %s", sender.getName(), stateOfState.name());
    }

    public enum States {
        ENTERED,
        EXITED
    }
}
