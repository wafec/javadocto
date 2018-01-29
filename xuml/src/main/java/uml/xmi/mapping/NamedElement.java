package uml.xmi.mapping;

public class NamedElement extends BaseElement {
    protected String mName;

    public NamedElement(String id, String name) {
        super(id);
        mName = name;
    }
}
