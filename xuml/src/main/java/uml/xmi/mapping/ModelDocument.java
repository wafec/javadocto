package uml.xmi.mapping;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.xml.sax.SAXException;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.HashMap;

public class ModelDocument {
    private BaseElement mRootElement;
    private HashMap<String, BaseElement> mElements = new HashMap<>();

    private static final String PACKAGE_TYPE = "uml:Package";
    private static final String CLASS_TYPE = "uml:Class";
    private static final String STATE_MACHINE_TYPE = "uml:StateMachine";
    private static final String REGION_TYPE = "uml:Region";
    private static final String TRANSITION_TYPE = "uml:Transition";
    private static final String TRIGGER_TYPE = "uml:Trigger";
    private static final String CONSTRAINT_TYPE = "uml:Constraint";
    private static final String OPAQUE_EXPRESSION_TYPE = "uml:OpaqueExpression";
    private static final String PSEUDOSTATE_TYPE = "uml:Pseudostate";
    private static final String STATE_TYPE = "uml:State";
    private static final String OPERATION_TYPE = "uml:Operation";
    private static final String PARAMETER_TYPE = "uml:Parameter";
    private static final String PRIMITIVE_TYPE = "uml:PrimitiveType";
    private static final String RECEPTION_TYPE = "uml:Reception";
    private static final String SIGNAL_TYPE = "uml:Signal";
    private static final String PROPERTY_TYPE = "uml:Property";
    private static final String SIGNAL_EVENT_TYPE = "uml:SignalEvent";
    private static final String OPAQUE_BEHAVIOR_TYPE = "uml:OpaqueBehavior";
    private static final String DATATYPE_TYPE = "uml:DataType";
    private static final String INTERFACE_TYPE = "uml:Interface";

    private static final String XMI_ID = "xmi:id";
    private static final String NAME_VALUE = "name";
    private static final String SOURCE_ID = "source";
    private static final String TARGET_ID = "target";
    private static final String GUARD_ID = "guard";
    private static final String HREF_VALUE = "href";
    private static final String SIGNAL_ID = "signal";
    private static final String EVENT_ID = "event";
    private static final String TYPE_ID = "type";

    public ModelDocument(InputStream inputStream) {
        try {
            parse(inputStream);
        } catch (SAXException | IOException | ParserConfigurationException ex) {
            System.out.println("Error on parse(): " + ex);
        }
    }

    private void parse(InputStream inputStream) throws SAXException, IOException, ParserConfigurationException {
        DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
        DocumentBuilder db = dbf.newDocumentBuilder();
        Document document = db.parse(inputStream);

        map(document.getDocumentElement(), null);
    }

    private void map(Element element, BaseElement parentElement) {
        if (element.hasAttribute("xmi:type")) {
            BaseElement newElement = parentElement;
            String type = element.getAttribute("xmi:type");
            switch (type) {
                case PACKAGE_TYPE:
                    newElement = getPackageElement(element);
                    break;
                case CLASS_TYPE:
                    newElement = getClazzElement(element);
                    break;
                case STATE_MACHINE_TYPE:
                    newElement = getStateMachineElement(element);
                    break;
                case REGION_TYPE:
                    newElement = getRegionElement(element);
                    break;
                case TRANSITION_TYPE:
                    newElement = getTransitionElement(element);
                    break;
                case TRIGGER_TYPE:
                    newElement = getTriggerElement(element);
                    break;
                case CONSTRAINT_TYPE:
                    newElement = getConstraintElement(element);
                    break;
                case OPAQUE_EXPRESSION_TYPE:
                    newElement = getOpaqueExpressionElement(element);
                    break;
                case PSEUDOSTATE_TYPE:
                    newElement = getPseudoStateElement(element);
                    break;
                case STATE_TYPE:
                    newElement = getStateElement(element);
                    break;
                case OPERATION_TYPE:
                    newElement = getOperationElement(element);
                    break;
                case PARAMETER_TYPE:
                    newElement = getParameterElement(element);
                    break;
                case PRIMITIVE_TYPE:
                    newElement = getPrimitiveTypeElement(element);
                    break;
                case RECEPTION_TYPE:
                    newElement = getReceptionElement(element);
                    break;
                case SIGNAL_TYPE:
                    newElement = getSignalElement(element);
                    break;
                case PROPERTY_TYPE:
                    newElement = getPropertyElement(element);
                    break;
                case SIGNAL_EVENT_TYPE:
                    newElement = getSignalEventElement(element);
                    break;
                case OPAQUE_BEHAVIOR_TYPE:
                    newElement = getOpaqueBehaviorElement(element);
                    break;
                case DATATYPE_TYPE:
                    newElement = getDataTypeElement(element);
                    break;
                case INTERFACE_TYPE:
                    newElement = getInterfaceElement(element);
                    break;
            }

            if (parentElement != newElement) {
                newElement.setParentId(parentElement.getId());
                parentElement.addChildId(newElement.getId());
                mElements.put(newElement.getId(), newElement);
                parentElement = newElement;
            }
        } else if (element.getTagName().equals("uml:Model")) {
            mRootElement = new ModelElement(element.getAttribute(XMI_ID), element.getAttribute(NAME_VALUE));
            mElements.put(mRootElement.getId(), mRootElement);
            parentElement = mRootElement;
        }

        for (int i = 0; i < element.getChildNodes().getLength(); i++) {
            Node node = element.getChildNodes().item(i);
            if (node.getNodeType() == Node.ELEMENT_NODE) {
                map((Element) node, parentElement);
            }
        }
    }

    private PackageElement getPackageElement(Element element) {
        return new PackageElement(element.getAttribute(XMI_ID), element.getAttribute(NAME_VALUE));
    }

    private ClazzElement getClazzElement(Element element) {
        return new ClazzElement(element.getAttribute(XMI_ID), element.getAttribute(NAME_VALUE));
    }

    private StateMachineElement getStateMachineElement(Element element) {
        return new StateMachineElement(element.getAttribute(XMI_ID), element.getAttribute(NAME_VALUE));
    }

    private RegionElement getRegionElement(Element element) {
        return new RegionElement(element.getAttribute(XMI_ID), element.getAttribute(NAME_VALUE));
    }

    private TransitionElement getTransitionElement(Element element) {
        TransitionElement transitionElement = new TransitionElement(element.getAttribute(XMI_ID), element.getAttribute(SOURCE_ID), element.getAttribute(TARGET_ID));
        if (element.hasAttribute(GUARD_ID)) {
            transitionElement.setGuardId(element.getAttribute(GUARD_ID));
        }
        return transitionElement;
    }

    private TriggerElement getTriggerElement(Element element) {
        return new TriggerElement(element.getAttribute(XMI_ID), element.getAttribute(EVENT_ID));
    }

    private ConstraintElement getConstraintElement(Element element) {
        return new ConstraintElement(element.getAttribute(XMI_ID));
    }

    private OpaqueExpressionElement getOpaqueExpressionElement(Element element) {
        Element bodyElement = getChildByTag(element, "body");
        String body = "";
        if (bodyElement != null) {
            body = bodyElement.getTextContent();
        }
        return new OpaqueExpressionElement(element.getAttribute(XMI_ID), body);
    }

    private PseudoStateElement getPseudoStateElement(Element element) {
        return new PseudoStateElement(element.getAttribute(XMI_ID), element.getAttribute(NAME_VALUE));
    }

    private StateElement getStateElement(Element element) {
        return new StateElement(element.getAttribute(XMI_ID), element.getAttribute(NAME_VALUE));
    }

    private OperationElement getOperationElement(Element element) {
        return new OperationElement(element.getAttribute(XMI_ID), element.getAttribute(NAME_VALUE));
    }

    private ParameterElement getParameterElement(Element element) {
        return new ParameterElement(element.getAttribute(XMI_ID), element.getAttribute(NAME_VALUE));
    }

    private PrimitiveTypeElement getPrimitiveTypeElement(Element element) {
        return new PrimitiveTypeElement(element.getAttribute(HREF_VALUE));
    }

    private ReceptionElement getReceptionElement(Element element) {
        return new ReceptionElement(element.getAttribute(XMI_ID), element.getAttribute(NAME_VALUE), element.getAttribute(SIGNAL_ID));
    }

    private SignalElement getSignalElement(Element element) {
        return new SignalElement(element.getAttribute(XMI_ID), element.getAttribute(NAME_VALUE));
    }

    private PropertyElement getPropertyElement(Element element) {
        PropertyElement propertyElement = new PropertyElement(element.getAttribute(XMI_ID), element.getAttribute(NAME_VALUE));
        if (element.hasAttribute(TYPE_ID)) {
            propertyElement.setTypeId(element.getAttribute(TYPE_ID));
        }
        return propertyElement;
    }

    private SignalEventElement getSignalEventElement(Element element) {
        return new SignalEventElement(element.getAttribute(XMI_ID), element.getAttribute(NAME_VALUE), element.getAttribute(SIGNAL_ID));
    }

    private OpaqueBehaviorElement getOpaqueBehaviorElement(Element element) {
        Element bodyElement = getChildByTag(element, "body");
        String body = "";
        if (body != null) {
            body = bodyElement.getTextContent();
        }
        return new OpaqueBehaviorElement(element.getAttribute(XMI_ID), body);
    }

    private DataTypeElement getDataTypeElement(Element element) {
        return new DataTypeElement(element.getAttribute(XMI_ID), element.getAttribute(NAME_VALUE));
    }

    private InterfaceElement getInterfaceElement(Element element) {
        return new InterfaceElement(element.getAttribute(XMI_ID), element.getAttribute(NAME_VALUE));
    }

    private Element getChildByTag(Element parent, String tagName) {
        for (int i = 0; i < parent.getChildNodes().getLength(); i++) {
            Node node = parent.getChildNodes().item(i);
            if (node.getNodeType() == Node.ELEMENT_NODE) {
                if (((Element) node).getTagName().equals(tagName)) {
                    return (Element) node;
                }
            }
        }
        return null;
    }

    public ModelElement getModelElement() {
        if (mRootElement != null && mRootElement instanceof ModelElement) {
            return (ModelElement) mRootElement;
        }
        return null;
    }

    public BaseElement findElement(String id) {
        if (mElements.containsKey(id)) {
            return mElements.get(id);
        }
        return null;
    }

    public ArrayList<BaseElement> getElements() {
        return new ArrayList<>(mElements.values());
    }
}
