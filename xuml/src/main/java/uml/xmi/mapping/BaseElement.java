package uml.xmi.mapping;

public class BaseElement {
    protected String mId;
    protected String mParentId;

    public BaseElement(String id) {
        mId = id;
    }

    public void setParentId(String parentId) {
        mParentId = parentId;
    }

    public String getId() {
        return mId;
    }
}
