package uml.xmi.mapping;

public class ReceptionElement extends NamedElement {
    private String mSignalEventId;

    public ReceptionElement(String id, String name, String signalEventId) {
        super(id, name);
        mSignalEventId = signalEventId;
    }

    public String getSignalEventId() {
        return mSignalEventId;
    }
}
