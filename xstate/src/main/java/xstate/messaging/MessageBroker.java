package xstate.messaging;

import java.util.ArrayList;

public final class MessageBroker {
    static final MessageBroker singleton = new MessageBroker();
    ArrayList<Subscription> subscriptions = new ArrayList<>();

    MessageBroker() {

    }

    public void addSubscription(Subscription subscription) {
        if (!subscriptions.contains(subscription))
            subscriptions.add(subscription);
    }

    public void removeSubscriber(Subscriber subscriber) {
        subscriptions.removeIf(s -> s.subscriber == subscriber);
    }

    public void route(Message message) {
        subscriptions.stream().forEach(s -> {
            if (s.filter == null || s.filter.test(message)) {
                s.subscriber.accept(message);
            }
        });
    }

    public static MessageBroker getSingleton() {
        return singleton;
    }
}
