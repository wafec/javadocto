package knowledge.testing;

import junit.framework.TestCase;

import java.util.ArrayList;

public class LogicalExpressionTokenizerTest extends TestCase {
    LogicalExpressionTokenizer tokenizer = new LogicalExpressionTokenizer();

    public void testExpressionOne() {
        String expression = "mPrice > mSize";
        ArrayList<LogicalExpressionTokenizer.Token> tokens;
        tokens = tokenizer.tokenize(expression);
        assertEquals(3, tokens.size());
    }

    public void testExpressionTwo() {
        String expression = "mPrice >= mSize";
        ArrayList<LogicalExpressionTokenizer.Token> tokens;
        tokens = tokenizer.tokenize(expression);
        assertEquals(3, tokens.size());
        assertEquals("mPrice", tokens.get(0).symbol);
        assertEquals(">=", tokens.get(1).symbol);
        assertEquals("mSize", tokens.get(2).symbol);
    }

    public void testExpressionThree() {
        String expression = "(mPrice + 1) == (mSize - 1)";
        ArrayList<LogicalExpressionTokenizer.Token> tokens;
        tokens = tokenizer.tokenize(expression);
        assertEquals(11, tokens.size());
    }

    public void testExpressionFour() {
        String expression = "(mPrice.home(arg1, arg2)) == (mSize - 1)";
        ArrayList<LogicalExpressionTokenizer.Token> tokens;
        tokens = tokenizer.tokenize(expression);
        assertEquals(9, tokens.size());
    }
}
