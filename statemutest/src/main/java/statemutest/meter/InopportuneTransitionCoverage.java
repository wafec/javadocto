package statemutest.meter;

import com.google.common.collect.Sets;
import org.apache.log4j.Logger;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.stream.Collectors;

public class InopportuneTransitionCoverage extends PairBasedCoverage {
    static Logger log  = Logger.getLogger(InopportuneTransitionCoverage.class);

    public ArrayList<Pair> coverageStateInputSet = new ArrayList<>();
    public ArrayList<Pair> exercisedStateInputSet = new ArrayList<>();

    @Override
    public void accept(CoverageMeter.States state, CoverageMeter meter) {
        if (state.equals(CoverageMeter.States.AFTER_EXECUTION)) {
            if (meter.transientExercisedArrows.size() == 0) {
                for (String stateId : meter.statesConfiguration.stream().map(s -> s.getId()).collect(Collectors.toList())) {
                    Pair pair = new Pair();
                    pair.instanceA = stateId;
                    pair.instanceB = meter.inputClassMapping.get(meter.sentInputs.get(0)).getCanonicalName();
                    exercisedStateInputSet.add(pair);
                }
            }
        }
    }

    @Override
    public GenericMeasure obtainMeasure() {
        HashSet<Pair> coverageSet = new HashSet<>(coverageStateInputSet);
        HashSet<Pair> exercisedSet = new HashSet<>(exercisedStateInputSet);
        Sets.SetView<Pair> view = Sets.intersection(coverageSet, exercisedSet);
        Measure measure = new Measure();
        measure.coverageStateInputSet = coverageStateInputSet;
        measure.exercisedStateInputSet = new ArrayList<>(view);
        measure.setRatio(coverageStateInputSet.size(), view.size());
        return measure;
    }

    public static class Measure extends GenericMeasure {
        public ArrayList<Pair> coverageStateInputSet;
        public ArrayList<Pair> exercisedStateInputSet;
    }
}
