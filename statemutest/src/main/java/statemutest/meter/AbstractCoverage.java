package statemutest.meter;

public abstract class AbstractCoverage {
    public abstract void accept(CoverageMeter.States state, CoverageMeter meter);
    public abstract GenericMeasure obtainMeasure();
}
