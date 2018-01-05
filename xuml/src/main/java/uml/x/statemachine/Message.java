package uml.x.statemachine;

public class Message {
    private Event mEvent;
    private InstanceProvider mInstanceProvider;

    public Message(InstanceProvider instanceProvider, Event event) {
        mEvent = event;
        mInstanceProvider = instanceProvider;
    }

    public int getEventCode() {
        return mEvent.getCode();
    }

    public Object getEventData() {
        return mEvent.getData();
    }
}
