package uml.xmi.mapping;

public class TransitionElement extends BaseElement {
    private String mSourceId;
    private String mTargetId;

    public TransitionElement(String id, String sourceId, String targetId) {
        super(id);
        mSourceId = sourceId;
        mTargetId = targetId;
    }
}
