package knowledge.modeling;

import junit.framework.TestCase;
import org.apache.commons.io.FileUtils;
import org.apache.log4j.LogManager;
import org.apache.log4j.Logger;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;

public class CodeGeneratorTest extends TestCase {
    Logger log = LogManager.getLogger(CodeGeneratorTest.class);

    File buildResourceAsTempFile(String resourcePath) {
        InputStream istream = getClass().getResourceAsStream(resourcePath);
        this.assertNotNull(istream);
        File tempFile = null;
        try {
            tempFile = Files.createTempFile("conductor-workload-model-", ".xml").toFile();
            tempFile.deleteOnExit();
            FileUtils.copyInputStreamToFile(istream, tempFile);
        } catch (IOException exception) {
            log.error(exception);
        }
        this.assertNotNull(tempFile);
        return tempFile;
    }

    public void testConductorWorkloadModel() {
        File conductorUML = buildResourceAsTempFile("/papyrus_conductor_test.xml");
        Finder finder = new Finder();
        finder.setFilePath(conductorUML.getPath());
        finder.load();
        CodeGenerator codeGen = new CodeGenerator();
        codeGen.setFinder(finder);
        codeGen.setForTesting(true);
        codeGen.generate();

        printCodeGen(codeGen);
    }

    void printCodeGen(CodeGenerator codeGen) {
        for (CodeGenerator.CodePiece codePiece : codeGen.getCodePieces()) {
            System.out.println();
            System.out.println("// " + codePiece.getName());
            System.out.println(codePiece.toString());
        }
    }

    public void testVendingMachine() {
        Finder finder = new Finder();
        finder.setFilePath("C:\\Users\\wallacec\\workspace-papyrus\\stackproject\\stackproject.uml");
        finder.load();
        CodeGenerator codeGenerator = new CodeGenerator();
        codeGenerator.setFinder(finder);
        codeGenerator.setForTesting(true);
        codeGenerator.generate();

        for (CodeGenerator.CodePiece codePiece : codeGenerator.getCodePieces()) {
            System.out.println();
            System.out.println("// " + codePiece.getName());
            System.out.println(codePiece.toString());
        }
    }

    public void testTheVmStates() {
        Finder finder = new Finder();
        finder.setFilePath("H:\\DATA\\development\\papyrus-workspace\\theVmStates\\theVmStates.uml");
        finder.load();
        CodeGenerator codeGenerator = new CodeGenerator();
        codeGenerator.setFinder(finder);
        codeGenerator.setForTesting(true);
        codeGenerator.generate();

        for (CodeGenerator.CodePiece codePiece : codeGenerator.getCodePieces()) {
            System.out.println();
            System.out.println("// " + codePiece.getName());
            System.out.println(codePiece.toString());
        }
    }
}
