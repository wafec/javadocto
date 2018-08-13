package statemutest.application;

import statemutest.testcase.GenericGeoTestCaseGenerator;
import statemutest.util.GenericHelper;

import java.util.Optional;
import java.util.stream.Collectors;

public class TestSetup {
    public GenericSetup generic;
    public MethodSpecificSetup method;

    public static abstract class MethodSpecificSetup {
        public abstract MethodSpecificSetup clone();
        public abstract void fill(MethodSpecificSetup other);
    }

    public <T extends MethodSpecificSetup> T getMethod(Class<T> clazz) {
        return clazz.cast(method);
    }

    public TestSetup overlap(TestSetup other) {
        TestSetup overlapped = other.clone();
        fill(overlapped);
        return overlapped;
    }

    void fill(TestSetup other) {
        if (other.generic == null && generic != null)
            other.generic = generic.clone();
        else
            fillGeneric(generic, other.generic);
        if (method != null) {
            if (other.method == null)
                other.method = method.clone();
            else if (method.getClass().equals(other.method.getClass()))
                method.fill(other.method);
            else
                other.method = method.clone();
        }
    }

    void fillGeneric(GenericSetup source, GenericSetup destination) {
        if (source == null)
            return;
        destination.xmiFilePath = GenericHelper.copyIfNotNull(source.xmiFilePath, destination.xmiFilePath);
        destination.classpath = GenericHelper.copyIfNotNull(source.classpath, destination.classpath);
        destination.instanceSpecFilePath = GenericHelper.copyIfNotNull(source.instanceSpecFilePath, destination.instanceSpecFilePath);
        destination.testClassQualifiedName = GenericHelper.copyIfNotNull(source.testClassQualifiedName, destination.testClassQualifiedName);
        destination.stateIdentitiesIdentifier = GenericHelper.copyIfNotNull(source.stateIdentitiesIdentifier, destination.stateIdentitiesIdentifier);
        destination.coverageTransitionSetIdentifier = GenericHelper.copyIfNotNull(source.coverageTransitionSetIdentifier, destination.coverageTransitionSetIdentifier);
        destination.stateIdentities = GenericHelper.mergeListsDistinct(source.stateIdentities, destination.stateIdentities);
        destination.coverageTransitionSet = GenericHelper.mergeListsDistinct(source.coverageTransitionSet, destination.coverageTransitionSet);
        destination.knowableStateIdentities = GenericHelper.mergeListsDistinct(source.knowableStateIdentities, destination.knowableStateIdentities);
        if (source.userDefinedStateInputMappings != null) {
            if (destination.userDefinedStateInputMappings == null)
                destination.userDefinedStateInputMappings = source.userDefinedStateInputMappings.stream().map(ud -> ud.clone()).collect(Collectors.toList());
            else {
                source.userDefinedStateInputMappings.stream().forEach(ud -> {
                    Optional<GenericGeoTestCaseGenerator.UserDefinedStateInputMapping> opt =
                            destination.userDefinedStateInputMappings.stream().filter(udo -> udo.isParamsEqual(ud)).findFirst();
                    if (opt.isPresent()) {
                        GenericGeoTestCaseGenerator.UserDefinedStateInputMapping udo = opt.get();
                        udo.lowerBound = ud.lowerBound;
                        udo.upperBound = ud.upperBound;
                    } else {
                        destination.userDefinedStateInputMappings.add(ud.clone());
                    }
                });
            }
        }
    }

    public TestSetup clone() {
        TestSetup cloned = new TestSetup();
        if (generic != null) {
            cloned.generic = generic.clone();
        }
        if (method != null) {
            cloned.method = method.clone();
        }
        return cloned;
    }
}
