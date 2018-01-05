package uml.x.statemachine;

public class Transition implements Checker {
    private State mDestination;
    private int mEventCode;
    private Guard mGuard = Guard.DEFAULT;
    private Action mEffect = Action.DEFAULT;

    public Transition(int eventCode, State destination) {
        mEventCode = eventCode;
        mDestination = destination;
    }

    @Override
    public boolean eval(Message message) {
        return message.getEventCode() == mEventCode && mGuard.eval(message);
    }

    public void act(Message message) {
        mEffect.run(message);
    }

    public void go(Message message) {
        mDestination.entering(message);
    }
}
