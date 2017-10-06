package geo.algorithm;

import java.util.ArrayList;
import java.util.List;

public class ParetoFrontier {
    private List<Element> elements;

    public ParetoFrontier() {
        this.elements = new ArrayList<>();
    }

    public boolean add(Sequence sequence, double[] objectivesRates, int iterationIndex) {
        Element element = new Element(sequence, objectivesRates, iterationIndex);
        int i = 0;
        while (i < this.elements.size()) {
            if (element.dominate(this.elements.get(i))) {
                this.elements.remove(i);
            } else if (this.elements.get(i).dominate(element)) {
                break;
            } else {
                i++;
            }
        }
        if (i >= this.elements.size()) {
            this.elements.add(element);
            return true;
        }
        return false;
    }

    public List<Element> getElements() {
        return this.elements;
    }

    public static class Element {
        private Sequence sequence;
        private double[] objectivesRates;
        private int iterationIndex;

        public Element(Sequence sequence, double[] objectivesRates, int iterationIndex) {
            this.sequence = sequence;
            this.objectivesRates = objectivesRates;
            this.iterationIndex = iterationIndex;
        }

        public boolean dominate(Element other) {
            int minLength = Math.min(other.getObjectivesRates().length, this.objectivesRates.length);
            int minCount = 0;
            for (int i = 0; i < minLength; i++) {
                if (other.getObjectivesRates()[i] < this.objectivesRates[i]) {
                    return false;
                } else if (this.objectivesRates[i] < other.getObjectivesRates()[i]) {
                    minCount++;
                }
            }
            return minCount > 0;
        }

        public double[] getObjectivesRates() {
            return this.objectivesRates;
        }

        public Sequence getSequence() {
            return this.sequence;
        }

        public int getIterationIndex() {
            return this.iterationIndex;
        }
    }
}
