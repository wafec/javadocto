package statemutest.testcase;

import geo.algorithm.BinaryInteger;
import junit.framework.TestCase;
import statemutest.modeling.JarGenerator;
import statemutest.testcase.TestCaseSet;
import statemutest.testcase.MgeoVslTestCaseGenerator;

import java.io.File;
import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Map;

public class MgeoVslTestCaseGeneratorTest extends TestCase {
    String xstateClasses = "H:\\WINDOWS\\Development\\javadocto\\xstate\\out\\production\\classes";
    String classpath = String.join(";", Arrays.asList(new String[] { xstateClasses }));

    public void testBasic() {
        JarGenerator jarGenerator = new JarGenerator(classpath);
        File jarFile = jarGenerator.generateJarFile("C:\\Users\\wallacec\\workspace-papyrus\\stackproject\\stackproject.uml");
        ArrayList<String> inputs = new ArrayList<>();
        inputs.add("util.Push");
        inputs.add("util.Pop");
        ArrayList<String> stateIdentities = new ArrayList<>();
        stateIdentities.add("_8mqxgD3fEeiVCInSg7lKsg");
        stateIdentities.add("_9t3DED3fEeiVCInSg7lKsg");
        stateIdentities.add("_-hv-ID3fEeiVCInSg7lKsg");
        stateIdentities.add("___si0D3fEeiVCInSg7lKsg");
        ArrayList<String> coverageTransitionSet = new ArrayList<>();
        coverageTransitionSet.add("_B_3q0D3gEeiVCInSg7lKsg");
        coverageTransitionSet.add("_C8NXQD3gEeiVCInSg7lKsg");
        coverageTransitionSet.add("_DengwD3gEeiVCInSg7lKsg");
        coverageTransitionSet.add("_EZ5dQD3gEeiVCInSg7lKsg");
        File instanceSpec = new File(
                System.class.getResource("/stackSpec.yaml").getPath());
        MgeoVslTestCaseGenerator testCaseGenerator = new MgeoVslTestCaseGenerator(jarFile,
                "util.Stack", instanceSpec, inputs, stateIdentities);
        TestCaseSet[] sets = testCaseGenerator.generateTestDataSequence(3.75, 1000, 10,
                new BinaryInteger.Domain(80, 200), coverageTransitionSet);
        System.out.println(sets);
    }

    public void testComplex() {
        String xmiPath = "C:\\Users\\wallacec\\workspace-papyrus\\test_complex\\test_complex.uml";
        JarGenerator jarGenerator = new JarGenerator(classpath);
        File jarFile = jarGenerator.generateJarFile(xmiPath);
        ArrayList<String> inputs = new ArrayList<String>(Arrays.asList(new String[] { "testcomplex.Event1", "testcomplex.Event2", "testcomplex.Event3" }));
        ArrayList<String> states = new ArrayList<>(Arrays.asList(new String[] { "_9F-AAHsREeixuYKLzTSveQ", "_966rAHsREeixuYKLzTSveQ", "_-MgKQHsREeixuYKLzTSveQ", "_-e-aUHsREeixuYKLzTSveQ" }));
        //ArrayList<String> states = new ArrayList<>();
        ArrayList<String> transitions = new ArrayList<>(Arrays.asList(new String[] { "__-DncHsREeixuYKLzTSveQ", "_AlI1kHsSEeixuYKLzTSveQ", "_A7m00HsSEeixuYKLzTSveQ" }));
        File instanceSpec = new File(
                System.class.getResource("/emptySpec.yaml").getPath());
        MgeoVslTestCaseGenerator testCaseGenerator = new MgeoVslTestCaseGenerator(jarFile,
                "testcomplex.TestClassComplex", instanceSpec, inputs, states);
        TestCaseSet[] sets = testCaseGenerator.generateTestDataSequence(0.95, 25000, 2,
                new BinaryInteger.Domain(30, 50), transitions);
        System.out.println(sets.length);
    }

    public void testComplexTwoScenarios() {
        String xmiPath = "C:\\Users\\wallacec\\workspace-papyrus\\test_complex\\test_complex.uml";
        JarGenerator jarGenerator = new JarGenerator(classpath);
        File jarFile = jarGenerator.generateJarFile(xmiPath);
        ArrayList<String> inputs = new ArrayList<String>(Arrays.asList(new String[] { "testcomplex.Event1", "testcomplex.Event2", "testcomplex.Event3" }));
        ArrayList<String> states = new ArrayList<>(Arrays.asList(new String[] { "_9F-AAHsREeixuYKLzTSveQ", "_966rAHsREeixuYKLzTSveQ", "_-MgKQHsREeixuYKLzTSveQ", "_-e-aUHsREeixuYKLzTSveQ" }));
        //ArrayList<String> states = new ArrayList<>();
        ArrayList<String> transitions = new ArrayList<>(Arrays.asList(new String[] { "__-DncHsREeixuYKLzTSveQ", "_AlI1kHsSEeixuYKLzTSveQ", "_A7m00HsSEeixuYKLzTSveQ" }));
        // second scenario
        transitions.addAll(Arrays.asList(new String[] { "_LWvs0HuoEei45J6_ICxhJg", "_UC6ywHuoEei45J6_ICxhJg", "_VX2lYHuoEei45J6_ICxhJg" }));
        File instanceSpec = new File(
                System.class.getResource("/emptySpec.yaml").getPath());
        MgeoVslTestCaseGenerator testCaseGenerator = new MgeoVslTestCaseGenerator(jarFile,
                "testcomplex.TestClassComplex", instanceSpec, inputs, states);
        TestCaseSet[] sets = testCaseGenerator.generateTestDataSequence(0.95, 25000, 10,
                new BinaryInteger.Domain(30, 50), transitions);
        System.out.println(sets.length);
    }

    public void testTheVmStates() {
        String xmiPath = "H:\\DATA\\development\\papyrus-workspace\\theVmStates\\theVmStates.uml";
        String spec = "H:\\DATA\\development\\papyrus-workspace\\theVmStates\\instanceSpec.yaml";
        JarGenerator jarGenerator = new JarGenerator(classpath);
        File jarFile = jarGenerator.generateJarFile(xmiPath);
        ArrayList<String> inputs = new ArrayList<>(Arrays.asList(new String[] { "root.signals.Build" }));
        ArrayList<String> states = new ArrayList<>(Arrays.asList(new String[] {
        }));
        ArrayList<String> transitions = new ArrayList<>(Arrays.asList(new String[] { "_1v5_sAauEemGqa4rhguvBA" }));

        MgeoVslTestCaseGenerator testCaseGenerator = new MgeoVslTestCaseGenerator(jarFile,
                "root.Vm", new File(spec), inputs, states);

        TestCaseSet[] sets = testCaseGenerator.generateTestDataSequence(0.95, 5000, 10,
                new BinaryInteger.Domain(30, 50), transitions);
        System.out.println(sets.length);
    }

    File getModelFolder(String projectName) {
        String value = System.getenv("PAPYRUS_WORKSPACE");
        File papyrusFolder = new File(value);
        File projectFolder = new File(papyrusFolder, projectName);
        return projectFolder;
    }

    void printSets(TestCaseSet[] sets) {
        int i = 0;
        for (TestCaseSet set : sets) {
            System.out.println("# SET: " + (i++));
            for (String metaKey : set.getMetadataKeys()) {
                System.out.println("# " + metaKey + ": " + set.getMetadataValue(metaKey));
            }
            for (Object test : set.getObjectDataSet()) {
                System.out.println("## SignalClass: " + test.getClass().getName());
                try {
                    Field[] fields = test.getClass().getFields();
                    for (int fi = 0; fi < fields.length; fi++) {
                        Field field = fields[fi];
                        Object fieldValue = field.get(test);
                        System.out.println("### " + field.getName() + ": " + fieldValue);
                    }
                } catch (Exception exception) {
                    // nothing to do here - THIS IS A TEST
                }
            }
        }
    }

    public void testGuardsTest() {
        File modelFolder = getModelFolder("guardsTest");
        String xmiPath = new File(modelFolder, "guardsTest.uml").getPath();
        String spec = new File(modelFolder, "guardsTest.spec.yaml").getPath();

        JarGenerator jarGenerator = new JarGenerator(classpath);
        File jarFile = jarGenerator.generateJarFile(xmiPath);

        ArrayList<String> inputs = new ArrayList<>(Arrays.asList(new String[] {
            "root.signals.Go",
            "root.signals.Continue",
            "root.signals.Stop"
        }));

        ArrayList<String> states = new ArrayList<>();
        ArrayList<String> transitions = new ArrayList<>(Arrays.asList(new String[] {
            "_Ya3owA9IEemsWaiz_NF3fw", //bar_continue_dummy
            "_CXIzMA9FEemsWaiz_NF3fw" // foo_go_bar
        }));

        MgeoVslTestCaseGenerator testCaseGenerator = new MgeoVslTestCaseGenerator(jarFile,
                "root.GuardsTest", new File(spec), inputs, states);

        TestCaseSet[] sets = testCaseGenerator.generateTestDataSequence(1.5, 5000, 1,
                new BinaryInteger.Domain(10, 20), transitions);

        printSets(sets);
    }
}
