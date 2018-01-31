package uml.xmi.mapping;

public class PropertyElement extends NamedElement {
    private String mTypeId;

    public PropertyElement(String id, String name) {
        super(id, name);
    }

    public void setTypeId(String typeId) {
        mTypeId = typeId;
    }

    public String getTypeId() {
        return mTypeId;
    }
}
