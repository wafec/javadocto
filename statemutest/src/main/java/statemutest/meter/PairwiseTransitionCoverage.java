package statemutest.meter;

import com.google.common.collect.Sets;
import org.apache.log4j.Logger;
import xstate.support.Arrow;

import java.util.ArrayList;
import java.util.HashSet;

public class PairwiseTransitionCoverage extends PairBasedCoverage {
    static Logger log = Logger.getLogger(PairwiseTransitionCoverage.class);

    public ArrayList<Pair> coverageTransitionIO = new ArrayList<>();
    public ArrayList<Pair> exercisedTransitionIO = new ArrayList<>();

    @Override
    public void accept(CoverageMeter.States state, CoverageMeter meter) {
        if (state.equals(CoverageMeter.States.POST_EXECUTION)) {
            for (int i = 0; i < meter.exercisedArrows.size() - 1; i++) {
                Arrow a = meter.exercisedArrows.get(i);
                Arrow b = meter.exercisedArrows.get(i + 1);
                Pair pair = new Pair();
                pair.instanceA = a.getId();
                pair.instanceB = b.getId();
                exercisedTransitionIO.add(pair);
            }
        }
    }

    @Override
    public GenericMeasure obtainMeasure() { ;
        HashSet<Pair> coverageHashSet = new HashSet<>(coverageTransitionIO);
        HashSet<Pair> exercisedHashSet = new HashSet<>(exercisedTransitionIO);
        Sets.SetView<Pair> view = Sets.intersection(coverageHashSet, exercisedHashSet);
        Measure measure = new Measure();
        measure.coverageTransitionIO = coverageTransitionIO;
        measure.exercisedTransitionIO = new ArrayList<>(view);
        measure.setRatio(coverageTransitionIO.size(), view.size());
        return measure;
    }



    public static class Measure extends GenericMeasure {
        public ArrayList<Pair> coverageTransitionIO;
        public ArrayList<Pair> exercisedTransitionIO;
    }
}
