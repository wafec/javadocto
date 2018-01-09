package uml.x.statemachine;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.stream.Collectors;

public class Tracker {
    private final ArrayList<TrackingLog> mTrackingLogs = new ArrayList<>();

    public void add(TrackingLog trackingLog) {
        mTrackingLogs.add(trackingLog);
    }

    public int size() {
        return mTrackingLogs.size();
    }

    public TrackingLog get(int index) {
        return mTrackingLogs.get(index);
    }

    public ArrayList<TrackingLog> filter(Class... classes) {
        return new ArrayList(mTrackingLogs.stream()
                .filter(tl -> Arrays.stream(classes).anyMatch(c -> c.isAssignableFrom(tl.getClass())))
                .collect(Collectors.toList()));
    }
}
