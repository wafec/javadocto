package statemutest.testcase;

import geo.algorithm.BinaryInteger;
import junit.framework.TestCase;
import statemutest.modeling.JarGenerator;
import statemutest.testcase.TestCaseSet;
import statemutest.testcase.MgeoVslTestCaseGenerator;

import java.io.File;
import java.util.ArrayList;
import java.util.Arrays;

public class MgeoVslTestCaseGeneratorTest extends TestCase {
    String xstateClasses = "C:\\Users\\wallacec\\Documents\\dev\\javadocto\\xstate\\out\\production\\classes";
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
                new BinaryInteger.Domain(80, 200, 8), coverageTransitionSet);
        System.out.println(sets);
    }

    public void testComplex() {
        String xmiPath = "C:\\Users\\wallacec\\workspace-papyrus\\test_complex\\test_complex.uml";
        JarGenerator jarGenerator = new JarGenerator(classpath);
        File jarFile = jarGenerator.generateJarFile(xmiPath);
        ArrayList<String> inputs = new ArrayList<String>(Arrays.asList(new String[] { "testcomplex.Event1", "testcomplex.Event2", "testcomplex.Event3" }));
        //ArrayList<String> states = new ArrayList<>(Arrays.asList(new String[] { "_9F-AAHsREeixuYKLzTSveQ", "_966rAHsREeixuYKLzTSveQ", "_-MgKQHsREeixuYKLzTSveQ", "_-e-aUHsREeixuYKLzTSveQ" }));
        ArrayList<String> states = new ArrayList<>();
        ArrayList<String> transitions = new ArrayList<>(Arrays.asList(new String[] { "__-DncHsREeixuYKLzTSveQ", "_AlI1kHsSEeixuYKLzTSveQ", "_A7m00HsSEeixuYKLzTSveQ" }));
        File instanceSpec = new File(
                System.class.getResource("/emptySpec.yaml").getPath());
        MgeoVslTestCaseGenerator testCaseGenerator = new MgeoVslTestCaseGenerator(jarFile,
                "testcomplex.TestClassComplex", instanceSpec, inputs, states);
        TestCaseSet[] sets = testCaseGenerator.generateTestDataSequence(0.95, 25000, 1,
                new BinaryInteger.Domain(3, 5, 7), transitions);
        System.out.println(sets);
    }
}
