package uml.xmi.mapping;

public class TransitionElement extends BaseElement {
    private String mSourceId;
    private String mTargetId;
    private String mGuardId;

    public TransitionElement(String id, String sourceId, String targetId) {
        super(id);
        mSourceId = sourceId;
        mTargetId = targetId;
    }

    public void setGuardId(String guardId) {
        mGuardId = guardId;
    }
}
