package xstate.modeling.messaging;

import xstate.messaging.Message;

public class ClassMessage extends Message<Object> {
    Types messageType;
    String messageBody;

    public static ClassMessage create(Object sender, Types messageType, String messageBody) {
        ClassMessage classMessage = new ClassMessage();
        classMessage.sender = sender;
        classMessage.messageType = messageType;
        classMessage.messageBody = messageBody;
        return classMessage;
    }

    public Types getMessageType() {
        return messageType;
    }

    public String getMessageBody() {
        return messageBody;
    }

    public enum Types {
        STATEMENT,
        PRE_CONDITION,
        POST_CONDITION
    }
}
