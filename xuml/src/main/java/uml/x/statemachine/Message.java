package uml.x.statemachine;

public class Message {
    private Event mEvent;
    private InstanceController mInstanceProvider;
    private Tracker mTracker;

    public Message(InstanceController instanceProvider, Event event, Tracker tracker) {
        mEvent = event;
        mInstanceProvider = instanceProvider;
        mTracker = tracker;
    }

    public int getEventCode() {
        return mEvent.getCode();
    }

    public Object getEventData() {
        return mEvent.getData();
    }

    public void putLog(TrackingLog trackingLog) {
        if (mTracker == null)
            return;
        mTracker.add(trackingLog);
    }
}
