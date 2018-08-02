package knowledge.testing;

import org.apache.log4j.Logger;

import java.util.ArrayList;
import java.util.HashMap;

public class DistanceBranchParser {
    static Logger log = Logger.getLogger(DistanceBranchParser.class);

    LogicalExpressionTokenizer tokenizer = new LogicalExpressionTokenizer();
    LogicalExpressionTreeFactory treeFactory = new LogicalExpressionTreeFactory();
    StringBuilder sb;
    ArrayList<LogicalExpressionTokenizer.Token> tokens;
    LogicalExpressionTreeFactory.TreeNode treeNode;
    HashMap<String, String> hashMap = new HashMap<>();

    public DistanceBranchParser() {
        hashMap.put("&&", "and");
        hashMap.put("||", "or");
        hashMap.put("<", "lessThan");
        hashMap.put(">", "greaterThan");
        hashMap.put("<=", "lessOrEqualThan");
        hashMap.put(">=", "greaterOrEqualThan");
        hashMap.put("==", "equalThan");
        hashMap.put("!=", "notEqualThan");
    }

    public String parse(String expression) {
        tokens = tokenizer.tokenize(expression);
        sb = new StringBuilder();
        treeNode = treeFactory.generateTree(tokens);
        treeFactory.walkingThrough(treeNode, (n) -> {
            // pre
            if (n.hasParenthesis) {
                sb.append("(");
            }
            if (n.tokens.size() > 0) {
                LogicalExpressionTokenizer.Token token = n.tokens.get(0);
                if (hashMap.containsKey(token.symbol)) {
                    sb.append("xstate.core.DistanceMath.");
                    sb.append(hashMap.get(token.symbol));
                    sb.append("(");
                }
            }
        }, (n) -> {
            // in
            if (n.tokens.size() > 0) {
                LogicalExpressionTokenizer.Token token = n.tokens.get(0);
                if (hashMap.containsKey(token.symbol)) {
                    sb.append(", ");
                } else {
                    for (LogicalExpressionTokenizer.Token t : n.tokens) {
                        sb.append(t.symbol);
                    }
                }
            }
        }, (n) -> {
            // post
            if (n.tokens.size() > 0) {
                LogicalExpressionTokenizer.Token token = n.tokens.get(0);
                if (hashMap.containsKey(token.symbol)) {
                    sb.append(")");
                }
            }
            if (n.hasParenthesis) {
                sb.append(")");
            }
        });

        log.debug("Distance parser from " + expression + " to " + sb.toString());

        return sb.toString();
    }
}
