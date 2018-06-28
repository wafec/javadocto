package statemutest.application;

import java.util.List;
import java.util.Map;

public class TestCaseObject {
    public List<TestInput> inputSet;
    public Map<String, String> metadata;

    public static class TestInput {
        public String qualifiedName;
        public Map<String, String> args;
    }
}
