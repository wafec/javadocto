package xstate.messaging;

public interface Subscriber {
    void accept(Message message);
}
