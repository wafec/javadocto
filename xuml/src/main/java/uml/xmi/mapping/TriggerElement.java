package uml.xmi.mapping;

public class TriggerElement extends BaseElement {
    private String mEventId;

    public TriggerElement(String id, String eventId) {
        super(id);
        mEventId = eventId;
    }
}
