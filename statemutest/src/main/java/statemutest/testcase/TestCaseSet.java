package statemutest.testcase;

import xstate.support.Input;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Set;

public class TestCaseSet {
    ArrayList<Input> inputDataSet;
    ArrayList objectDataSet;
    HashMap<String, Object> metadata = new HashMap<>();

    public TestCaseSet(ArrayList<Input> inputDataSet, ArrayList objectDataSet) {
        this.inputDataSet = inputDataSet;
        this.objectDataSet = objectDataSet;
    }

    public ArrayList<Input> getInputDataSet() {
        return inputDataSet;
    }

    public ArrayList getObjectDataSet() {
        return objectDataSet;
    }

    public void putMetadata(String key, Object value) {
        metadata.put(key, value);
    }

    public Object getMetadataValue(String key) {
        return metadata.get(key);
    }

    public Set<String> getMetadataKeys() {
        return metadata.keySet();
    }
}
