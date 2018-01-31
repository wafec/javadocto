package uml.xmi.mapping;

public class PrimitiveTypeElement extends BaseElement {
    private String mHref;

    public PrimitiveTypeElement(String href) {
        super(getVolatileId());
        mHref = href;
    }

    public String getHref() {
        return mHref;
    }
}
