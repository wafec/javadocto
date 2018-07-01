package xstate.core;

public class Identity {
    String id = "__default_id__";
    int userCode = -1;
    String classifierId = "__general_classifier__";

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

    public void setClassifierId(String classifierId) {
        this.classifierId = classifierId;
    }

    public String getClassifierId() {
        return classifierId;
    }
}
