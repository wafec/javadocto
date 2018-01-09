package uml.x.statemachine;

public class Action implements Code {
    public static final Action DEFAULT = new Action();

    @Override
    public void run(Message message) { }
}
