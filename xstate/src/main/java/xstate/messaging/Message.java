package xstate.messaging;

public class Message <T> {
    protected T sender;

    public T getSender() {
        return sender;
    }
}
