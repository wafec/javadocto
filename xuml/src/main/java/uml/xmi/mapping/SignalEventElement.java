package uml.xmi.mapping;

public class SignalEventElement extends NamedElement {
    private String mSignalId;

    public SignalEventElement(String id, String name, String signalId) {
        super(id, name);
        mSignalId = signalId;
    }
}
