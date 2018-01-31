package uml.x.statemachine;

public class Transition implements Checker {
    private State mDestination;
    private int mEventCode;
    private Guard mGuard = Guard.DEFAULT;
    private Action mEffect = Action.DEFAULT;
    private int mId;

    public Transition(int id, int eventCode, State destination) {
        mId = id;
        mEventCode = eventCode;
        mDestination = destination;
    }

    @Override
    public boolean eval(Message message) {
        message.putLog(new EvaluateLog());
        return message.getEventCode() == mEventCode && mGuard.eval(message);
    }

    public void act(Message message) {
        mEffect.run(message);
    }

    public void go(Message message) {
        message.putLog(new TraversedLog());
        mDestination.entering(message);
    }

    public int getId() {
        return mId;
    }

    public class TraversedLog extends TrackingLog {
        private final static String TAG = "Traversed";

        public TraversedLog() {
            super(TAG, mId);
        }
    }

    public class EvaluateLog extends TrackingLog {
        private final static String TAG = "Evaluate";

        public EvaluateLog() {
            super(TAG, mId);
        }
    }

    public void setGuard(Guard guard) {
        mGuard = guard;
    }

    public void setEffect(Action action) {
        mEffect = action;
    }
}
