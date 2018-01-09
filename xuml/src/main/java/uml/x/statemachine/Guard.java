package uml.x.statemachine;

public class Guard implements Checker {
    public static final Guard DEFAULT = new Guard();

    @Override
    public boolean eval(Message message) {
        return true;
    }

    public class BranchDistanceLog extends TrackingLog {
        private static final String TAG = "BranchDistance";

        public BranchDistanceLog(double branchDistance) {
            super(TAG, branchDistance);
        }
    }
}
