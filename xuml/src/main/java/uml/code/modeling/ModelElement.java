package uml.code.modeling;

public abstract class ModelElement {
    protected String mId;

    public void setId(String id) {
        mId = id;
    }

    public String getId() {
        return mId;
    }
}
