package knowledge.testing;

import java.lang.reflect.Array;
import java.util.ArrayList;
import java.util.function.Consumer;

public class LogicalExpressionTreeFactory {
    private String[] symbols = {
        "||", "&&", "<", ">", "<=", ">=", "==", "!="
    };

    public class TreeNode {
        public TreeNode right, left;
        public ArrayList<LogicalExpressionTokenizer.Token> tokens = new ArrayList<>();
        public boolean hasParenthesis = false;
    }

    public TreeNode generateTree(ArrayList tokens) {
        TreeNode node = new TreeNode();
        ArrayList<Object> compacted = compressTokens(decompressTokens(tokens));
        int i = 0;
        while (i < symbols.length) {
            int findex = findBySymbol(compacted, symbols[i]);
            if (findex != -1) {
                node.tokens.add((LogicalExpressionTokenizer.Token) compacted.get(findex));
                node.left = generateTree(new ArrayList(compacted.subList(0, findex)));
                node.right = generateTree(new ArrayList(compacted.subList(findex + 1, compacted.size())));
                return node;
            }
            i++;
        }
        if (compacted.size() == 1) {
            if (compacted.get(0) instanceof ArrayList) {
                ArrayList list = (ArrayList) compacted.get(0);
                if (list.size() > 2) {
                    //node.tokens.add((LogicalExpressionTokenizer.Token) list.get(0));
                    //node.left = new TreeNode();
                    //node.left.tokens.add((LogicalExpressionTokenizer.Token) list.get(list.size() - 1));
                    node.right = generateTree(new ArrayList(list.subList(1, list.size() - 1)));
                    node.hasParenthesis = true;
                    return node;
                }
            }
        }
        node.tokens.addAll(tokens);
        return node;
    }

    private ArrayList<Object> compressTokens(ArrayList tokens) {
        ArrayList<Object> aux = new ArrayList<>();
        for (int i = 0; i < tokens.size(); i++) {
            LogicalExpressionTokenizer.Token token = (LogicalExpressionTokenizer.Token) tokens.get(i);
            if (token.type == LogicalExpressionTokenizer.Token.Type.OPENING_PARENTHESIS) {
                int openingParenthesisCounter = 1;
                ArrayList<LogicalExpressionTokenizer.Token> subList = new ArrayList<>();
                subList.add(token);
                for (int j = i + 1; j < tokens.size(); j++, i++) {
                    LogicalExpressionTokenizer.Token jtoken = (LogicalExpressionTokenizer.Token) tokens.get(j);
                    if (jtoken.type == LogicalExpressionTokenizer.Token.Type.CLOSING_PARENTHESIS) {
                        if (openingParenthesisCounter == 1)
                            break;
                        openingParenthesisCounter--;
                    }
                    if (jtoken.type == LogicalExpressionTokenizer.Token.Type.OPENING_PARENTHESIS) {
                        openingParenthesisCounter++;
                    }
                    subList.add(jtoken);
                }
                if (i + 1 < tokens.size())
                    subList.add((LogicalExpressionTokenizer.Token) tokens.get(i + 1));
                aux.add(subList);
                i += 1;
            } else {
                aux.add(token);
            }
        }
        return aux;
    }

    private ArrayList decompressTokens(ArrayList compacted) {
        ArrayList aux = new ArrayList();
        for (Object item : compacted) {
            if (item instanceof ArrayList) {
                aux.addAll(((ArrayList) item));
            } else {
                aux.add(item);
            }
        }
        return aux;
    }

    private int findBySymbol(ArrayList<Object> list, String symbol) {
        for (int i = 0; i < list.size(); i++) {
            Object item = list.get(i);
            if (item instanceof LogicalExpressionTokenizer.Token) {
                LogicalExpressionTokenizer.Token token = (LogicalExpressionTokenizer.Token) item;
                if (token.symbol.equals(symbol)) {
                    return i;
                }
            }
        }
        return -1;
    }

    public void walkingThrough(TreeNode node, Consumer<TreeNode> pre, Consumer<TreeNode> in, Consumer<TreeNode> post) {
        if (pre != null)
            pre.accept(node);
        if (node.left != null) {
            walkingThrough(node.left, pre, in, post);
        }
        if (in != null)
            in.accept(node);
        if (node.right != null) {
            walkingThrough(node.right, pre, in, post);
        }
        if (post != null)
            post.accept(node);
    }
}
