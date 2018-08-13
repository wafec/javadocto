package statemutest.application;

import knowledge.modeling.Finder;
import org.apache.log4j.Logger;
import statemutest.testcase.GenericGeoTestCaseGenerator;

import java.util.*;
import java.util.stream.Collectors;

public class GenericSetup {
    static Logger log = Logger.getLogger(GenericSetup.class);

    public String xmiFilePath;
    public String instanceSpecFilePath;
    public String classpath;
    public List<String> inputQualifiedNames;
    public List<String> stateIdentities;
    public List<String> knowableStateIdentities;
    public String stateIdentitiesIdentifier;
    public List<String> coverageTransitionSet;
    public String coverageTransitionSetIdentifier;
    public String testClassQualifiedName;
    public List<GenericGeoTestCaseGenerator.UserDefinedStateInputMapping> userDefinedStateInputMappings;

    public List<String> getCoverageTransitionSetForTesting() {
        if (coverageTransitionSetIdentifier == null)
            return coverageTransitionSet;

        if (!coverageTransitionSetIdentifier.equals("id")) {
            Finder finder = Finder.newInstance(xmiFilePath);
            final ArrayList<String> res = new ArrayList<>();
            finder.getElements().stream().forEach(e -> {
                if (e.getTagName().equals("transition")) {
                    String attribute = "";
                    switch (coverageTransitionSetIdentifier) {
                        case "name":
                            if (e.hasAttribute("name"))
                                attribute = e.getAttribute("name");
                            break;
                    }
                    if (coverageTransitionSet.contains(attribute)) {
                        res.add(e.getAttribute("xmi:id"));
                        log.debug("Transition ID=" + e.getAttribute("xmi:id") + ", Name=\""+attribute+"\"");
                    }
                }
            });
            return res;
        } else {
            return coverageTransitionSet;
        }
    }

    public List<String> getStateIdentitiesForTesting() {
        return getGenericStateIdentitiesForTesting(stateIdentities);
    }

    public List<String> getKnowableStateIdentitiesForTesting() {
        return getGenericStateIdentitiesForTesting(knowableStateIdentities);
    }

    List<String> getGenericStateIdentitiesForTesting(final List<String> genericStateIdentities) {
        if (genericStateIdentities == null)
            return new ArrayList<String>();
        if (stateIdentitiesIdentifier == null)
            return genericStateIdentities;

        if (!stateIdentitiesIdentifier.equals("id")) {
            Finder finder = Finder.newInstance(xmiFilePath);
            final ArrayList<String> res = new ArrayList<>();
            finder.getElements().stream().forEach(e -> {
                if (e.hasAttribute("xmi:type") && e.getAttribute("xmi:type").equals("uml:State")) {
                    String attribute = "";
                    switch (stateIdentitiesIdentifier) {
                        case "name":
                            if (e.hasAttribute("name"))
                                attribute = e.getAttribute("name");
                            break;
                    }
                    if (genericStateIdentities.contains(attribute)) {
                        res.add(e.getAttribute("xmi:id"));
                        log.debug("States ID=" + e.getAttribute("xmi:id") + ", Name=\"" + attribute + "\"");
                    }
                }
            });
            return res;
        } else {
            return genericStateIdentities;
        }
    }

    String findStateIdByName(Finder finder, final String name) {
        String id = finder.getElements().stream().filter(e -> {
            return e.hasAttribute("xmi:type") && e.getAttribute("xmi:type").equals("uml:State") &&
                    e.hasAttribute("name") && e.getAttribute("name").equals(name);
        }).findFirst().get().getAttribute("xmi:id");
        return id;
    }

    public List<GenericGeoTestCaseGenerator.UserDefinedStateInputMapping> getUserDefinedStateInputMappingsForTesting() {
        if (stateIdentitiesIdentifier == null)
            return userDefinedStateInputMappings;
        if (userDefinedStateInputMappings == null)
            return null;
        if (stateIdentitiesIdentifier.equals("id"))
            return userDefinedStateInputMappings;
        List<GenericGeoTestCaseGenerator.UserDefinedStateInputMapping> res = new ArrayList<>();
        Finder finder = Finder.newInstance(xmiFilePath);
        for (final GenericGeoTestCaseGenerator.UserDefinedStateInputMapping ud : userDefinedStateInputMappings) {
            GenericGeoTestCaseGenerator.UserDefinedStateInputMapping usedInstance = ud.clone();
            switch (stateIdentitiesIdentifier) {
                case "name":
                    try {
                        String id = findStateIdByName(finder, ud.stateIdentity);
                        usedInstance.stateIdentity = id;
                    } catch (NoSuchElementException exception) {
                        log.warn("State identity " + ud.stateIdentity + " could not be found");
                    }
                    break;
            }
            res.add(usedInstance);
        }
        return res;
    }

    public Map<String, String> getStatesMapping() {
        Map<String, String> map = new HashMap<>();
        Finder finder = Finder.newInstance(xmiFilePath);

        finder.getElements().stream().filter(e -> {
            return e.hasAttribute("xmi:type") && e.getAttribute("xmi:type").equals("uml:States");
        }).forEach(e -> {
            String identity = e.getAttribute("xmi:id");
            if (stateIdentitiesIdentifier != null && !stateIdentitiesIdentifier.equals("id")) {
                switch (stateIdentitiesIdentifier) {
                    case "name":
                        identity = e.getAttribute("name");
                        break;
                }
            }
            map.put(e.getAttribute("xmi:id"), identity);
        });
        return map;
    }

    public Map<String, String> getTransitionsMapping() {
        Map<String, String> map = new HashMap<>();
        Finder finder = Finder.newInstance(xmiFilePath);
        finder.getElements().stream().filter(e ->{
            return e.getTagName().equals("transition");
        }).forEach(e -> {
            String identity = e.getAttribute("xmi:id");
            if (coverageTransitionSetIdentifier != null && !coverageTransitionSetIdentifier.equals("id")) {
                switch (coverageTransitionSetIdentifier) {
                    case "name":
                        identity = e.getAttribute("name");
                        break;
                }
            }
            map.put(e.getAttribute("xmi:id"), identity);
        });
        return map;
    }

    public GenericSetup clone() {
        GenericSetup cloned = new GenericSetup();
        cloned.xmiFilePath = xmiFilePath;
        cloned.instanceSpecFilePath = instanceSpecFilePath;
        if (inputQualifiedNames != null)
            cloned.inputQualifiedNames = new ArrayList<>(inputQualifiedNames);
        if (stateIdentities != null)
            cloned.stateIdentities = new ArrayList<>(stateIdentities);
        if (coverageTransitionSet != null)
            cloned.coverageTransitionSet = new ArrayList<>(coverageTransitionSet);
        cloned.stateIdentitiesIdentifier = stateIdentitiesIdentifier;
        cloned.coverageTransitionSetIdentifier = coverageTransitionSetIdentifier;
        cloned.testClassQualifiedName = testClassQualifiedName;
        if (userDefinedStateInputMappings != null) {
            cloned.userDefinedStateInputMappings = userDefinedStateInputMappings.stream().map(ud -> {
                return ud.clone();
            }).collect(Collectors.toList());
        }
        cloned.classpath = classpath;
        if (knowableStateIdentities != null)
            cloned.knowableStateIdentities = new ArrayList<>(knowableStateIdentities);
        return cloned;
    }
}
