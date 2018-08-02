package geo.algorithm;

public abstract class Algorithm {
    protected double tau;

    public Algorithm(double tau) {
        this.tau = tau;
    }

    public void run() {
        initialization();
        do {
            doMutation();
            sortCandidatesSolutions();
            chooseCandidateSolution();
            update();
        } while (!stop());
        cleanup();
    }

    protected abstract void initialization();
    protected abstract boolean stop();
    protected abstract void doMutation();
    protected abstract void sortCandidatesSolutions();
    protected abstract void chooseCandidateSolution();
    protected abstract void update();

    protected void cleanup() {

    }
}
