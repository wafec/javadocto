package statemutest.testcase;

import geo.algorithm.BinaryInteger;
import junit.framework.TestCase;
import statemutest.modeling.JarGenerator;

import java.io.File;
import java.util.ArrayList;
import java.util.Arrays;

public class MgeoVslTestCaseGeneratorTest extends TestCase {
    public void testBasic() {
        String xstateClasses = "C:\\Users\\wallacec\\Documents\\dev\\javadocto\\xstate\\out\\production\\classes";
        String knowledgeClasses = "C:\\Users\\wallacec\\Documents\\dev\\javadocto\\knowledge\\out\\production\\classes";
        String classpath = String.join(";", Arrays.asList(new String[] { xstateClasses, knowledgeClasses }));
        JarGenerator jarGenerator = new JarGenerator(classpath);
        File jarFile = jarGenerator.generateJarFile("C:\\Users\\wallacec\\workspace-papyrus\\stackproject\\stackproject.uml");
        ArrayList<String> inputs = new ArrayList<>();
        inputs.add("util.Push");
        inputs.add("util.Pop");
        ArrayList<String> stateIdentities = new ArrayList<>();
        ArrayList<String> coverageTransitionSet = new ArrayList<>();
        coverageTransitionSet.add("_B_3q0D3gEeiVCInSg7lKsg");
        coverageTransitionSet.add("_C8NXQD3gEeiVCInSg7lKsg");
        coverageTransitionSet.add("_DengwD3gEeiVCInSg7lKsg");
        coverageTransitionSet.add("_EZ5dQD3gEeiVCInSg7lKsg");
        File instanceSpec = new File(
                System.class.getResource("/stackSpec.yaml").getPath());
        MgeoVslTestCaseGenerator testCaseGenerator = new MgeoVslTestCaseGenerator(jarFile,
                "util.Stack", instanceSpec, inputs, stateIdentities);
        testCaseGenerator.generateTestDataSequence(3.75, 1000, 10,
                new BinaryInteger.Domain(80, 200, 8), coverageTransitionSet);
    }
}
