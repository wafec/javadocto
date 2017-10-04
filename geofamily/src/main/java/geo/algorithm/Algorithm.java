package geo.algorithm;

public abstract class Algorithm {
    public void run() {
        initialization();
        do {
            doMutation();
            sortCandidatesSolutions();
            chooseCandidateSolution();
            update();
        } while (!stop());
    }

    protected abstract void initialization();
    protected abstract boolean stop();
    protected abstract void doMutation();
    protected abstract void sortCandidatesSolutions();
    protected abstract void chooseCandidateSolution();
    protected abstract void update();
}
