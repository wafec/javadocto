package statemutest.modeling;

import junit.framework.TestCase;

import java.util.Arrays;

public class JarGeneratorTest extends TestCase {
    public void testBase() {
        String xstateClasses = "C:\\Users\\wallacec\\Documents\\dev\\javadocto\\xstate\\out\\production\\classes";
        String knowledgeClasses = "C:\\Users\\wallacec\\Documents\\dev\\javadocto\\knowledge\\out\\production\\classes";
        String classpath = String.join(";", Arrays.asList(new String[] { xstateClasses, knowledgeClasses }));
        JarGenerator jarGenerator = new JarGenerator(classpath);
        jarGenerator.generateJarFile("C:\\Users\\wallacec\\workspace-papyrus\\stackproject\\stackproject.uml");
    }
}
