package knowledge.testing;

import junit.framework.TestCase;

public class DistanceBranchParserTest extends TestCase {
    public void testBasicExpression() {
        DistanceBranchParser parser = new DistanceBranchParser();
        String result = parser.parse("((a + b) < c) && (c == 0 || a == 1)");
        assertEquals("knowledge.util.DistanceMath.and((knowledge.util.DistanceMath.lessThan((a+b), c)), (knowledge.util.DistanceMath.or(knowledge.util.DistanceMath.equalThan(c, 0), knowledge.util.DistanceMath.equalThan(a, 1))))", result);
    }
}
