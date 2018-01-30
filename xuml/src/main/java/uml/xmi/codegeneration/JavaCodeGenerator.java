package uml.xmi.codegeneration;

import uml.xmi.mapping.*;

import java.io.File;
import java.io.IOException;
import java.io.PrintWriter;

public class JavaCodeGenerator {
    private File mDirectory;
    private int mIndentationIndex = 0;
    private ModelDocument mModelDocument;
    private StringBuilder mStringBuilder;
    private File mCurrentDirectory;

    private final int mIndentationTabCount = 4;

    public JavaCodeGenerator() {

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
        mStringBuilder.append(indentation() + text + "\n");
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
}
