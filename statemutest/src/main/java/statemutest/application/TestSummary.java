package statemutest.application;

import java.util.List;
import java.util.Map;

public class TestSummary {
    public String fictitiousName;
    public Map<String, String> states;
    public Map<String, String> transitions;
    public String statesIdentifier;
    public String transitionsIdentifier;
    public List<String> generatedTestCases;

    public String returnMatchedResultIfExists(String identity) {
        if (states != null && states.containsKey(identity)) {
            return states.get(identity);
        }
        if (transitions != null && transitions.containsKey(identity)) {
            return transitions.get(identity);
        }
        return identity;
    }
}
