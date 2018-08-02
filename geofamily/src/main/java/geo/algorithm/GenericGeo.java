package geo.algorithm;

import java.time.Duration;
import java.time.Instant;
import java.time.temporal.TemporalUnit;
import java.util.*;
import java.util.concurrent.TimeUnit;

public abstract class GenericGeo extends Algorithm {
    protected Sequence currentSequence;
    protected double[] currentObjectivesRates;
    protected double[] bestObjectivesRates;
    protected Objective[] objectives;
    protected BinaryInteger.Domain[] searchDomain;
    protected Solution[] currentSolutions;
    protected int totalOfBits;
    protected Random randomGenerator;

    protected TimerTask monitor;

    Timer monitorTimer;

    public GenericGeo(double tau, Objective[] objectives, BinaryInteger.Domain[] searchDomain) {
        super(tau);
        this.objectives = objectives;
        this.searchDomain = searchDomain;
        this.totalOfBits = BinaryInteger.Domain.computeTotalOfBits(this.searchDomain);
        this.randomGenerator = new Random();
    }

    @Override
    protected void initialization() {
        this.currentSequence = new Sequence(this.searchDomain);
        this.currentSequence.sample(this.randomGenerator);
        this.bestObjectivesRates = new double[this.objectives.length];
        for (int i = 0; i < objectives.length; i++) {
            this.bestObjectivesRates[i] = this.objectives[i].eval(this.currentSequence);
        }
        this.currentObjectivesRates = Arrays.copyOfRange(this.bestObjectivesRates, 0, this.bestObjectivesRates.length);

        if (monitor != null) {
            monitorTimer = new Timer();
            monitorTimer.scheduleAtFixedRate(monitor, TimeUnit.SECONDS.toMillis(3), TimeUnit.SECONDS.toMillis(10));
        }
    }

    @Override
    protected void doMutation() {
        this.currentSolutions = new Solution[this.totalOfBits];
        int solutionIndex = 0;
        for (int i = 0; i < this.currentSequence.getNumberOfProjectVariables(); i++) {
            BinaryInteger projectVariable = this.currentSequence.getProjectVariables()[i];
            for (int j = 0; j < projectVariable.getNumberOfBits(); j++) {
                BinaryInteger candidate = projectVariable.copy();
                candidate.flip(j);
                Solution solution = new Solution(
                        candidate,
                        projectVariable,
                        i,
                        j,
                        solutionIndex,
                        this.objectives.length
                );
                this.currentSequence.applySolution(solution);
                for (int k = 0; k < this.objectives.length; k++) {
                    solution.setObjectiveRate(k, this.objectives[k].eval(this.currentSequence));
                }
                this.currentSequence.restore(solution);
                this.currentSolutions[solutionIndex++] = solution;
            }
        }
    }

    protected void calculateCurrentObjectivesRates() {
        for (int i = 0; i < this.objectives.length; i++) {
            this.currentObjectivesRates[i] = this.objectives[i].eval(this.currentSequence);
        }
    }

    abstract class AbstractMonitor extends TimerTask {
        Instant start = Instant.now();
        float progress;

        Duration calculateElapsed() {
            Instant now = Instant.now();
            long diff = Duration.between(start, now).toMillis();
            long elapsed = (long) ((1.0001 - progress) * diff / progress);
            return Duration.ofMillis(elapsed);
        }
    }

    @Override
    protected void cleanup() {
        super.cleanup();
        if (monitor != null) {
            monitor.cancel();
            monitorTimer.cancel();
        }
    }
}
