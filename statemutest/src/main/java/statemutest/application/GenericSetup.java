package statemutest.application;

import knowledge.modeling.Finder;
import org.apache.log4j.Logger;

import java.util.ArrayList;
import java.util.List;

public class GenericSetup {
    static Logger log = Logger.getLogger(GenericSetup.class);

    public String xmiFilePath;
    public String instanceSpecFilePath;
    public String classpath;
    public List<String> inputQualifiedNames;
    public List<String> stateIdentities;
    public String stateIdentitiesIdentifier;
    public List<String> coverageTransitionSet;
    public String coverageTransitionSetIdentifier;
    public String testClassQualifiedName;

    public List<String> getCoverageTransitionSetForTesting() {
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
                    if (stateIdentities.contains(attribute)) {
                        res.add(e.getAttribute("xmi:id"));
                        log.debug("State ID=" + e.getAttribute("xmi:id") + ", Name=\"" + attribute + "\"");
                    }
                }
            });
            return res;
        } else {
            return stateIdentities;
        }
    }
}
