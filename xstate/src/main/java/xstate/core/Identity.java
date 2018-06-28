package xstate.core;

public class Identity {
    String id;
    int userCode = -1;

    public void setId(String id) {
        this.id = id;
    }

    public String getId() {
        return id;
    }

    public void setUserCode(int userCode) {
        this.userCode = userCode;
    }

    public int getUserCode() {
        return userCode;
    }
}
