package knowledge.testing;

import junit.framework.TestCase;

import java.util.ArrayList;

public class LogicalExpressionTreeTest extends TestCase {
    private int numberOfNodes;

    private void printTokens(ArrayList<LogicalExpressionTokenizer.Token> tokens) {
        for (LogicalExpressionTokenizer.Token token : tokens) {
            System.out.print(token.symbol + "");
        }
    }

    public void testBasicExpression() {
        LogicalExpressionTreeFactory factory = new LogicalExpressionTreeFactory();
        LogicalExpressionTokenizer tokenizer = new LogicalExpressionTokenizer();
        String expression = "a + b < c && a == 1 || b >= 3";
        ArrayList tokens = tokenizer.tokenize(expression);
        LogicalExpressionTreeFactory.TreeNode treenode = factory.generateTree(tokens);
        numberOfNodes = 0;
        factory.walkingThrough(treenode, null, (n) -> {
            printTokens(n.tokens);
            numberOfNodes++;
        }, null);
        assertEquals(11, numberOfNodes);
    }

    public void testComplexExpression() {
        LogicalExpressionTreeFactory factory = new LogicalExpressionTreeFactory();
        LogicalExpressionTokenizer tokenizer = new LogicalExpressionTokenizer();
        String expression = "((a + b) < ((c)) && ((a == 1) || b >= 3))";
        ArrayList tokens = tokenizer.tokenize(expression);
        LogicalExpressionTreeFactory.TreeNode treenode = factory.generateTree(tokens);
        numberOfNodes = 0;
        factory.walkingThrough(treenode, (n) -> { if (n.hasParenthesis) System.out.print("("); }, (n) -> {
            printTokens(n.tokens);
            numberOfNodes++;
        }, (n) -> { if (n.hasParenthesis) System.out.print(")"); });

    }
}
