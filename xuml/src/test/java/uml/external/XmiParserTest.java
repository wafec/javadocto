package uml.external;

import org.junit.Assert;
import org.junit.Test;
import uml.code.modeling.ModelElement;

import java.io.InputStream;
import java.util.ArrayList;

public class XmiParserTest {
    @Test
    public void testClazz() {
        InputStream istream = XmiParserTest.class.getResourceAsStream("example_01.xml");
        XmiParser xmiParser = new XmiParser();
        ArrayList<ModelElement> modelElements = xmiParser.fromInputStream(istream);
        Assert.assertEquals(1, modelElements.size());
    }
}
