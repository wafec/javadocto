package uml.x.statemachine;

public class Guard implements Checker {
    public static final Guard DEFAULT = new Guard();

    @Override
    public boolean eval(Message message) {
        return true;
    }
}
