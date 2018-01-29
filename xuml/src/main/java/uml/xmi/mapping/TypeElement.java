package uml.xmi.mapping;

public class TypeElement extends BaseElement {
    private String mType;
    private String mHref;

    public TypeElement(String type, String href) {
        super("");
        mType = type;
        mHref = href;
    }
}
