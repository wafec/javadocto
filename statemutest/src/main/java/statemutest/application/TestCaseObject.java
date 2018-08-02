package statemutest.application;

import org.apache.log4j.Logger;

import java.lang.reflect.Field;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class TestCaseObject {
    static Logger log = Logger.getLogger(TestCaseObject.class);

    public String fictitiousName;
    public List<TestInput> inputSet;
    public Map<String, String> metadata;

    public static class TestInput {
        public String qualifiedName;
        public Map<String, String> args;
        public List<TestExpected> expectedSet;
    }

    public static class TestExpected {
        public String qualifiedName;
        public Map<String, String> extras;
    }

    public static Map<String, String> collectAttributeValuePairs(Object instance) {
        Map<String, String> map = new HashMap<>();
        for (Field field : instance.getClass().getFields()) {
            try {
                map.put(field.getName(), field.get(instance).toString());
            } catch (IllegalAccessException exception) {
                log.error(exception.getMessage());
            }
        }
        return map;
    }
}
