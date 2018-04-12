package knowledge.modeling;

import junit.framework.TestCase;

public class CodeGeneratorTest extends TestCase {
    public void testVendingMachine() {
        Finder finder = new Finder();
        finder.setFilePath("C:\\Users\\wallacec\\workspace-papyrus\\stackproject\\stackproject.uml");
        finder.load();
        CodeGenerator codeGenerator = new CodeGenerator();
        codeGenerator.setFinder(finder);
        codeGenerator.generate();

        for (CodeGenerator.CodePiece codePiece : codeGenerator.getCodePieces()) {
            System.out.println();
            System.out.println("// " + codePiece.getName());
            System.out.println(codePiece.toString());
        }
    }
}
