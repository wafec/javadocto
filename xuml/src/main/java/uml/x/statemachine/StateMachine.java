package uml.x.statemachine;

public class StateMachine extends State implements EventHandler {
    public StateMachine(String name) {
        super(name);
    }

    @Override
    public void handle(Message message) {
        mRegions.forEach(r -> r.handle(message));
    }
}
