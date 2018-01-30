package uml.xmi.codegeneration;

import uml.xmi.mapping.*;

import java.io.File;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.Iterator;

public class JavaCodeGenerator {
    private File mDirectory;
    private int mIndentationIndex = 0;
    private ModelDocument mModelDocument;
    private StringBuilder mStringBuilder;
    private File mCurrentDirectory;

    private int mIndentationTabCount;

    public static final int DEFAULT_INDENTATION_TAB_COUNT = 4;

    public JavaCodeGenerator() {
        this(DEFAULT_INDENTATION_TAB_COUNT);
    }

    public JavaCodeGenerator(int indentationTabCount) {
        mIndentationIndex = indentationTabCount;
    }

    public void generateCode(File directory, ModelDocument model) {
        mDirectory = directory;
        mModelDocument = model;
        visit(model.getModelElement());
    }

    private void visit(ModelElement modelElement) {
        for (String childId : modelElement.getChildIds()) {
            BaseElement element = mModelDocument.findElement(childId);
            if (element != null) {
                if (element instanceof PackageElement) {
                    visit((PackageElement) element);
                } else if (element instanceof ClazzElement) {
                    visit((ClazzElement) element);
                }
            }
        }
    }

    private void visit(PackageElement packageElement) {
        for (String childId : packageElement.getChildIds()) {
            BaseElement element = mModelDocument.findElement(childId);
            if (element != null) {
                if (element instanceof PackageElement) {
                    visit((PackageElement) element);
                } else if (element instanceof ClazzElement) {
                    visit((ClazzElement) element);
                }
            }
        }
    }

    private void visit(ClazzElement clazzElement) {
        mStringBuilder = new StringBuilder();
        String packagePath = getPackagePath(clazzElement);
        writeLine("package " + packagePath + ";");
        writeLine("");
        writeLine("public class " + clazzElement.getName() + " {");
        indent();
        ArrayList<BaseElement> childElements = getElementsFromIds(clazzElement.getChildIds());
        childElements.stream().filter(e -> e instanceof PropertyElement).forEach(e -> {
            visit((PropertyElement) e);
        });
        writeLine("");
        childElements.stream().filter(e -> e instanceof OperationElement).forEach(e -> {
           visit((OperationElement) e);
        });
        unindent();
        writeLine("}");
        createPath(packagePath);
        File javaFile = new File(mCurrentDirectory, clazzElement.getName() + ".java");
        try {
            PrintWriter writer = new PrintWriter(javaFile, "UTF-8");
            writer.write(mStringBuilder.toString());
            writer.close();
        } catch (IOException ex) {
            System.out.println("Error on visit(ClazzElement): " + ex);
        }
    }

    // TO-DO: add other types
    private void visit(PropertyElement propertyElement) {
        PrimitiveTypeElement primitiveTypeElement = (PrimitiveTypeElement) getElementsFromIds(propertyElement.getChildIds())
                .stream().filter(e -> e instanceof PrimitiveTypeElement)
                .findFirst().get();
        write("public ");
        visit(primitiveTypeElement);
        write(" " + propertyElement.getName());
        write(";");
        writeLine("");
    }

    private void visit(PrimitiveTypeElement primitiveTypeElement) {
        String javaType = getJavaPrimitiveType(primitiveTypeElement.getHref());
        write(javaType);
    }

    private void visit(OperationElement operationElement) {
        write("public void " + operationElement.getName() + "(");
        ArrayList<BaseElement> childElements = getElementsFromIds(operationElement.getChildIds());
        Iterator<BaseElement> it = childElements.stream().filter(e -> e instanceof ParameterElement).iterator();
        int index = 0;
        while (it.hasNext()) {
            BaseElement element = it.next();
            if (element instanceof ParameterElement) {
                if (index != 0) {
                    write(", ");
                }
                visit((ParameterElement) element);
            }
            index++;
        }
        write(") {");
        indent();
        // TO-DO: some logic for operations and logs
        unindent();
        write("}");
        writeLine("");
    }

    private void visit(ParameterElement parameterElement) {
        PrimitiveTypeElement primitiveTypeElement = (PrimitiveTypeElement) getElementsFromIds(parameterElement.getChildIds())
                .stream()
                .filter(e -> e instanceof PrimitiveTypeElement)
                .findFirst()
                .get();
        visit(primitiveTypeElement);
        write(" " + parameterElement.getName());
    }

    private String indentation() {
        StringBuilder stringBuilder = new StringBuilder();
        for (int i = 0; i < mIndentationTabCount * mIndentationIndex; i++) {
            stringBuilder.append(" ");
        }
        return stringBuilder.toString();
    }

    private String getPackagePath(BaseElement baseElement) {
        StringBuilder stringBuilder = new StringBuilder();
        do {
            if (baseElement.getParentId() != null && !baseElement.getParentId().isEmpty()) {
                baseElement = mModelDocument.findElement(baseElement.getParentId());
                if (baseElement instanceof PackageElement) {
                    stringBuilder.insert(0, ((PackageElement) baseElement).getName() + ".");
                }
            }
        } while(baseElement != null);
        if (stringBuilder.toString().length() > 1) {
            return stringBuilder.toString().substring(0, stringBuilder.toString().length() - 1);
        } else {
            return "";
        }
    }

    private void createPath(String packagePath) {
        String path = packagePath.replace(".", File.pathSeparator);
        mCurrentDirectory = new File(mDirectory, path);
        if (!mCurrentDirectory.exists()) {
            mCurrentDirectory.mkdirs();
        }
    }

    private void writeLine(String text) {
        write(text + "\n");
    }

    private void write(String text) {
        mStringBuilder.append(indentation() + text);
    }

    private void indent() {
        mIndentationIndex++;
    }

    private void unindent() {
        mIndentationIndex--;
        if (mIndentationIndex < 0) {
            mIndentationIndex = 0;
        }
    }

    private ArrayList<BaseElement> getElementsFromIds(ArrayList<String> childIds) {
        ArrayList<BaseElement> elements = new ArrayList<>();
        for (String childId : childIds) {
            elements.add(mModelDocument.findElement(childId));
        }
        return elements;
    }

    private String getJavaPrimitiveType(String href) {
        if (href.endsWith("Integer")) {
            return "int";
        }
        return "int";
    }
}
