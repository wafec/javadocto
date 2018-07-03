package xstate.support.messaging;

import xstate.messaging.Message;
import xstate.support.Output;

public class OutputMessage extends Message<Output> {
    String descriptor;
    String[] args;

    public static OutputMessage create(Output sender, String descriptor, String[] args) {
        OutputMessage message = new OutputMessage();
        message.sender = sender;
        message.descriptor = descriptor;
        message.args = args;
        return message;
    }

    public String getDescriptor() {
        return descriptor;
    }

    public String[] getArgs() {
        return args;
    }
}
