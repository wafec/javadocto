package uml.x.statemachine;

public class StateMachine extends State implements EventHandler {
    @Override
    public void handle(Message message) {
        mRegions.forEach(r -> r.handle(message));
    }
}
