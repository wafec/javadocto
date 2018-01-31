package uml.xmi.codegeneration;

import uml.xmi.mapping.ModelDocument;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;

public class Main {
    public static void main(String... args) throws FileNotFoundException {
        ModelDocument modelDocument = new ModelDocument(new FileInputStream(new File("/home/venturus/Temp/papyrus_model01.uml")));
        JavaCodeGenerator javaCodeGenerator = new JavaCodeGenerator();
        javaCodeGenerator.generateCode(new File("/home/venturus/Temp"), modelDocument);
    }
}
