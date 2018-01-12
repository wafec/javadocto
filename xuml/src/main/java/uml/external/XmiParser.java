package uml.external;

import org.w3c.dom.*;
import org.xml.sax.SAXException;
import uml.code.modeling.ModelElement;
import uml.code.modeling.clazz.Clazz;
import uml.code.modeling.clazz.Operation;
import uml.code.modeling.clazz.Parameter;
import uml.code.modeling.statemachine.StateDiagram;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.function.Consumer;

public class XmiParser implements Parser {
    private ArrayList<ModelElement> mModelElements;

    @Override
    public ArrayList<ModelElement> fromInputStream(InputStream inputStream) {
        mModelElements = new ArrayList<>();
        Document document = null;
        try {
            DocumentBuilderFactory builderFactory = DocumentBuilderFactory.newInstance();
            DocumentBuilder builder = builderFactory.newDocumentBuilder();
            document = builder.parse(inputStream);
        } catch (ParserConfigurationException | IOException | SAXException e) {
            System.out.println("Exception calling fromInputStream(): " + e);
        }

        if (document != null)
            parseAll(document.getDocumentElement(), "");
        return mModelElements;
    }

    protected void parseAll(Node n, String packagePrefix)  {
        if (n != null) {
            if (isClass(n)) {
                Element e = (Element) n;
                Clazz clazz = new Clazz(e.getAttribute("name"), packagePrefix);
                parseClass(clazz, n);
                mModelElements.add(clazz);
                return;
            } else if (isPackage(n)) {
                Element e = (Element) n;
                if (!packagePrefix.isEmpty()) {
                    packagePrefix += ".";
                }
                packagePrefix += e.getAttribute("name");
            }

            final String p = packagePrefix;
            iterateOnChildren(n, c -> parseAll(c, p));
        }
    }

    protected void parseClass(Clazz clazz, Node n) {
        if (n != null) {
            if (isOperation(n)) {
                Element e = (Element) n;
                Operation operation = new Operation(e.getAttribute("name"));
                parseOperation(operation, n);
                clazz.addOperation(operation);
                return;
            }
            if (isStateMachine(n)) {
                StateDiagram stateMachine = new StateDiagram();
                parseStateMachine(stateMachine, n);
                clazz.defineStateDiagram(stateMachine);
                return;
            }
            iterateOnChildren(n, c -> parseClass(clazz, c));
        }
    }

    protected void parseOperation(Operation operation, Node n) {
        if (n != null) {
            if (isParameter(n)) {
                Element element = (Element) n;
                Parameter.Direction direction = Parameter.Direction.IN;
                if (element.hasAttribute("direction")) {
                    if (element.getAttribute("direction").equals("out")) {
                        direction = Parameter.Direction.OUT;
                    }
                }
                String type = parseParameterType(n);
                operation.addParameter(element.getAttribute("name"), type, direction);
                return;
            }
            iterateOnChildren(n, c -> parseOperation(operation, c));
        }
    }

    protected String parseParameterType(Node n) {
        String type = "Object";

        return type;
    }

    protected void parseStateMachine(StateDiagram stateMachine, Node n) {

    }

    protected boolean isPackage(Node n) {
        if (n.getNodeType() == Node.ELEMENT_NODE) {
            Element element = (Element) n;
            if (element.getTagName().equals("packagedElement")) {
                return element.getAttribute("xmi:type").equals("uml:Package");
            }
        }
        return false;
    }

    protected boolean isClass(Node n) {
        if (n.getNodeType() == Node.ELEMENT_NODE) {
            Element element = (Element) n;
            if (element.getTagName().equals("packagedElement")) {
                Attr typeAttr = element.getAttributeNode("xmi:type");
                return typeAttr.getValue().equals("uml:Class");
            }
        }
        return false;
    }

    protected boolean isOperation(Node n) {
        if (n.getNodeType() == Node.ELEMENT_NODE) {
            Element element = (Element) n;
            if (element.getTagName().equals("ownedOperation")) {
                return element.getAttribute("xmi:type").equals("uml:Operation");
            }
        }
        return false;
    }

    protected boolean isParameter(Node n) {
        if (n.getNodeType() == Node.ELEMENT_NODE) {
            Element element = (Element) n;
            if (element.getTagName().equals("ownedParameter")) {
                return element.getAttribute("xmi:type").equals("uml:Parameter");
            }
        }
        return false;
    }

    protected boolean isStateMachine(Node n) {
        if (n.getNodeType() == Node.ELEMENT_NODE) {
            Element element = (Element) n;
            if (element.getTagName().equals("ownedBehavior")) {
                return element.getAttribute("xmi:type").equals("uml:StateMachine");
            }
        }
        return false;
    }

    protected void iterateOnChildren(Node n, Consumer<Node> consumer) {
        NodeList nodeList = n.getChildNodes();
        for (int index = 0; index < nodeList.getLength(); index++) {
            Node c = nodeList.item(index);
            consumer.accept(c);
        }
    }
}
