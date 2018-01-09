package uml.x.statemachine;

public class TrackingLog {
    private String mTag;
    private Object mData;

    public TrackingLog(String tag, Object data) {
        mTag = tag;
        mData = data;
    }

    public String getTag() {
        return mTag;
    }

    public Object getData() {
        return mData;
    }
}
