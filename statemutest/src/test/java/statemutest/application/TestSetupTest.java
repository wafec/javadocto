package statemutest.application;

import com.esotericsoftware.yamlbeans.YamlWriter;
import junit.framework.TestCase;
import statemutest.testcase.GenericGeoTestCaseGenerator;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;

public class TestSetupTest extends TestCase {
    public void testWriteYaml() throws IOException {
        TestSetup setup = new TestSetup();
        setup.generic = new GenericSetup();
        setup.generic.xmiFilePath = "FILE";
        TestSetup.MgeoVslSetup method;
        setup.method = method = new TestSetup.MgeoVslSetup();
        method.tau = 3.75;

        YamlWriter writer = new YamlWriter(new FileWriter("test-file-setup.yaml"));
        writer.getConfig().setClassTag("setup", TestSetup.class);
        writer.getConfig().setClassTag("stateInputMapping", GenericGeoTestCaseGenerator.UserDefinedStateInputMapping.class);
        writer.getConfig().setClassTag("conf", GenericSetup.class);
        writer.getConfig().setClassTag("mgeovsl", TestSetup.MgeoVslSetup.class);
        writer.write(setup);
        writer.close();
        new File("test-file-setup.yaml").delete();
    }
}
