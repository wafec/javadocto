package xstate.messaging;

import java.util.function.Predicate;

public class Subscription {
    public Subscriber subscriber;
    public Predicate<Message> filter;
}
