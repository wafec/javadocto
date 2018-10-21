package knowledge.modeling;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.xml.sax.SAXException;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.function.Consumer;
import java.util.function.Predicate;

public class Finder {
    String filePath;
    ArrayList<Element> roots = new ArrayList<>();
    ArrayList<Element> elements = new ArrayList<>();
    HashMap<String, Element> elementsHashMap = new HashMap<>();

    public Finder() {

    }

    public void setFilePath(String filePath) {
        this.filePath = filePath;
    }

    public void load() {
        Document document = null;

        try {
            InputStream is = new FileInputStream(filePath);
            DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
            DocumentBuilder db = dbf.newDocumentBuilder();
            document = db.parse(is);
        } catch (IOException ex) {

        } catch (SAXException ex) {

        } catch (ParserConfigurationException ex) {

        }

        if (document != null) {
            startProcessing(document);
        }
    }

    void startProcessing(Document document) {
        Element root = document.getDocumentElement();
        roots.add(root);
        visit(root);
    }

    void visit(Element element) {
        if (element != null) {
            if (!elements.contains(element)) {
                elements.add(element);
            }
            if (element.hasAttribute("xmi:id")) {
                if (!elementsHashMap.containsKey(element.hasAttribute("xmi:id"))) {
                    elementsHashMap.put(element.getAttribute("xmi:id"), element);
                }
            }

            if (element.hasChildNodes()) {
                NodeList nodeList = element.getChildNodes();
                for (int i = 0; i < nodeList.getLength(); i++) {
                    Node node = nodeList.item(i);
                    if (node.getNodeType() == Node.ELEMENT_NODE) {
                        visit((Element) node);
                    }
                }
            }
        }
    }

    public ArrayList<Element> getRoots() {
        return roots;
    }

    public ArrayList<Element> getElements() {
        return elements;
    }

    public void forEach(Element startingPoint, Predicate<Element> predicate, Consumer<Element> consumer) {
        forEach(startingPoint, predicate, consumer, true);
    }

    public void forEach(Element startingPoint, Predicate<Element> predicate, Consumer<Element> consumer, boolean stopOnFirstMatch) {
        NodeList nodeList = startingPoint.getChildNodes();
        for (int i = 0; i < nodeList.getLength(); i++) {
            Node node = nodeList.item(i);
            if (node.getNodeType() == Node.ELEMENT_NODE) {
                if (predicate.test((Element) node)) {
                    consumer.accept((Element) node);
                    if (!stopOnFirstMatch) {
                        forEach((Element) node, predicate, consumer, stopOnFirstMatch);
                    }
                } else {
                    forEach((Element) node, predicate, consumer, stopOnFirstMatch);
                }
            }
        }
    }

    public ArrayList<Element> getPathFrom(Element element, Predicate<Element> predicate) {
        ArrayList<Element> path = new ArrayList<>();
        if (predicate.test(element))
            path.add(element);
        Node parent = element.getParentNode();
        while (parent != null) {
            if (parent.getNodeType() == Node.ELEMENT_NODE) {
                if (predicate.test((Element) parent))
                    path.add(0, (Element) parent);
            }
            parent = parent.getParentNode();
        }
        return path;
    }

    public Element getElementByHash(String hash) {
        if (elementsHashMap.containsKey(hash)) {
            return elementsHashMap.get(hash);
        }
        return null;
    }

    public static Finder newInstance(String filePath) {
        Finder finder = new Finder();
        finder.setFilePath(filePath);
        finder.load();
        return finder;
    }
}
