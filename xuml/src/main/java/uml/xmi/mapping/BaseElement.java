package uml.xmi.mapping;

import java.util.ArrayList;

public class BaseElement {
    protected String mId;
    protected String mParentId;
    protected final ArrayList<String> mChildIds = new ArrayList<>();

    public BaseElement(String id) {
        mId = id;
    }

    public void setParentId(String parentId) {
        mParentId = parentId;
    }

    public void addChildId(String childId) {
        mChildIds.add(childId);
    }

    public String getId() {
        return mId;
    }

    public ArrayList<String> getChildIds() {
        return new ArrayList<>(mChildIds);
    }

    public String getParentId() {
        return mParentId;
    }

    protected static int sTempId = 0;

    protected static String getVolatileId() {
        return String.format("BID%07d", sTempId++);
    }
}
