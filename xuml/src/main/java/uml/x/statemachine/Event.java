package uml.x.statemachine;

public class Event {
    private int mCode;
    private Object mData;

    public Event(int code, Object data) {
        mCode = code;
        mData = data;
    }

    public int getCode() {
        return mCode;
    }

    public Object getData() {
        return mData;
    }
}
