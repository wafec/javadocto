package uml.external;

import uml.code.modeling.ModelElement;

import java.io.InputStream;
import java.util.ArrayList;

public interface Parser {
    ArrayList<ModelElement> fromInputStream(InputStream inputStream);
}
