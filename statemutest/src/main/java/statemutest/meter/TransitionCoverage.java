package statemutest.meter;

import com.google.common.collect.Sets;
import org.apache.log4j.Logger;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.stream.Collectors;

public class TransitionCoverage extends AbstractCoverage {
    static Logger log = Logger.getLogger(TransitionCoverage.class);

    public ArrayList<String> coverageTransitionSet = new ArrayList<>();
    public ArrayList<String> exercisedTransitionSet = new ArrayList<>();

    @Override
    public void accept(CoverageMeter.States state, CoverageMeter meter) {
        if (state.equals(CoverageMeter.States.POST_EXECUTION)) {
            exercisedTransitionSet.addAll(
                    meter.exercisedArrows.stream().map(a -> a.getId()).collect(Collectors.toList())
            );
        }
    }

    @Override
    public GenericMeasure obtainMeasure() {
        HashSet<String> coverageHashSet = new HashSet<>(coverageTransitionSet);
        HashSet<String> exercisedHashSet = new HashSet<>(exercisedTransitionSet);
        Sets.SetView<String> view = Sets.intersection(coverageHashSet, exercisedHashSet);
        Measure measure = new Measure();
        measure.coverageTransitionSet = coverageTransitionSet;
        measure.exercisedTransitionSet = new ArrayList<>(view);
        measure.setRatio(coverageTransitionSet.size(), view.size());
        return measure;
    }

    public static class Measure extends GenericMeasure {
        public ArrayList<String> exercisedTransitionSet;
        public ArrayList<String> coverageTransitionSet;
    }
}
