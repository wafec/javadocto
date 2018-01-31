package uml.xmi.codegeneration;

import uml.xmi.mapping.*;

import java.io.File;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.stream.Collectors;

public class JavaCodeGenerator {
    private File mDirectory;
    private int mIndentationIndex;
    private ModelDocument mModelDocument;
    private StringBuilder mStringBuilder;
    private File mCurrentDirectory;
    private int mTransitionCount = 0;

    private int mIndentationTabCount;

    public static final int DEFAULT_INDENTATION_TAB_COUNT = 4;

    public JavaCodeGenerator() {
        this(DEFAULT_INDENTATION_TAB_COUNT);
    }

    public JavaCodeGenerator(int indentationTabCount) {
        mIndentationTabCount = indentationTabCount;
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
        writeLine("private uml.x.StateMachine mOwnedBehavior;");
        writeLine("private final java.util.HashMap<Integer, String> mTransitionIdsMap = new java.util.HashMap<>();");
        writeLine("public " + clazzElement.getName() + "() {");
        indent();
        writeLine("onStateMachineCreated();");
        unindent();
        writeLine("}");
        ArrayList<BaseElement> childElements = getElementsFromIds(clazzElement.getChildIds());
        List<BaseElement> propertyElements = childElements.stream().filter(e -> e instanceof PropertyElement).collect(Collectors.toList());
        List<BaseElement> operationElements = childElements.stream().filter(e -> e instanceof OperationElement).collect(Collectors.toList());
        if (propertyElements.size() > 0) {
            propertyElements.forEach(e -> {
                visit((PropertyElement) e);
            });
        }
        if (operationElements.size() > 0) {
            operationElements.forEach(e -> {
                visit((OperationElement) e);
            });
        }
        List<BaseElement> stateMachineElements = childElements.stream().filter(e -> e instanceof StateMachineElement)
                .collect(Collectors.toList());
        writeLine("private void onStateMachineCreated() {");
        indent();
        if (stateMachineElements.size() > 0) {
            visit((StateMachineElement) stateMachineElements.stream().findFirst().get());
        }
        unindent();
        writeLine("}");
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
        write("public ", true);
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
        write("public void " + operationElement.getName() + "(", true);
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
        writeLine("", false);
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

    private void visit(StateMachineElement stateMachineElement) {
        writeLine("mOwnedBehavior = new uml.x.StateMachine(\"" +
            stateMachineElement.getName() + "\");");
        getElementsFromIds(stateMachineElement.getChildIds()).stream().filter(e -> e instanceof RegionElement).forEach(e -> {
            visit((RegionElement) e);
            writeLine("mOwnedBehavior.addRegion(" + ((RegionElement) e).getName() + ");");
        });
    }

    private void visit(RegionElement regionElement) {
        ArrayList<BaseElement> childElements = getElementsFromIds(regionElement.getChildIds());
        StateElement initialState = getInitialState(regionElement);
        List<BaseElement> stateElements = childElements.stream().filter(e -> e instanceof StateElement).collect(Collectors.toList());
        stateElements.stream().map(e -> (StateElement) e).forEach(s -> {
            writeLine("uml.x.State " + s.getName() + " = new uml.x.State(\"" + s.getName() + "\");");
        });
        writeLine("uml.x.Region " + regionElement.getName() + " = new uml.x.Region(" + initialState.getName() + ");");
        stateElements.stream().map(e -> (StateElement) e).forEach(s -> {
            writeLine(regionElement.getName() + ".addState(" + s.getName() + ");");
        });
        List<BaseElement> transitionElements = childElements.stream().filter(e -> e instanceof TransitionElement).collect(Collectors.toList());
        transitionElements.stream().map(e -> (TransitionElement) e).forEach(t -> {
            visit(t);
        });
    }

    private void visit(TransitionElement transitionElement) {
        // TO-DO: set Transition id and event code properly
        writeLine("uml.x.Transition " + "t" + transitionElement.getId() + " = new uml.x.Transition(" +
            mTransitionCount + ");");
        writeLine("mTransitionIdsMap.put(" + mTransitionCount++ + ", " + "\"" + transitionElement.getId() + "\");");
    }

    private StateElement getInitialState(RegionElement regionElement) {
        ArrayList<BaseElement> childElements = getElementsFromIds(regionElement.getChildIds());
        PseudoStateElement initialState = (PseudoStateElement)
                childElements.stream().filter(e -> e instanceof PseudoStateElement).findFirst().get();
        TransitionElement initialTransition = (TransitionElement)
                childElements.stream().filter(e -> e instanceof TransitionElement)
                .map(e -> (TransitionElement) e)
                .filter(t -> t.getSourceId().equals(initialState.getId()))
                .findFirst().get();
        StateElement realInitialState = (StateElement)
                childElements.stream().filter(e -> e instanceof StateElement)
                .filter(e -> e.getId().equals(initialTransition.getTargetId()))
                .findFirst().get();
        return realInitialState;
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
            } else {
                baseElement = null;
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

    private void writeLine(String text, boolean indent) {
        if (indent) {
            write(indentation(), false);
        }
        write(text + "\n", false);
    }

    private void write(String text, boolean indent) {
        if (indent) {
            mStringBuilder.append(indentation());
        }
        mStringBuilder.append(text);
    }

    private void writeLine(String text) {
        writeLine(text, true);
    }

    private void write(String text) {
        write(text, false);
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
