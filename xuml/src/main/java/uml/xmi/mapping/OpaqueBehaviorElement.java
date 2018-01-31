package uml.xmi.mapping;

public class OpaqueBehaviorElement extends BaseElement
{
    private String mBody;

    public OpaqueBehaviorElement(String id, String body) {
        super(id);
        mBody = body;
    }

    public String getBody() {
        return mBody;
    }
}
