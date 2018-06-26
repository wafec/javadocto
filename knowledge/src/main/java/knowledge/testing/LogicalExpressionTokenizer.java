package knowledge.testing;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.stream.Collectors;

public class LogicalExpressionTokenizer {
    String[] breakers = {
        ">", "<", "=", "(", ")", " ", "&", "|"
    };

    String[] aggregated = {
        ">=", "<=", "==", "||", "&&"
    };

    public LogicalExpressionTokenizer() {
        Arrays.sort(breakers);
    }

    public ArrayList<Token> tokenize(String logicalExpression) {
        ArrayList<Token> tokens = new ArrayList<Token>();
        StringBuilder conc = new StringBuilder();
        int startPosition = 0;
        for (int i = 0; i < logicalExpression.length(); i++) {
            String c = "" + logicalExpression.charAt(i);
            int search = Arrays.binarySearch(breakers, c);
            if (search >= 0 && search < breakers.length && breakers[search].equals(c)) {
                Token tokenOne = new Token();
                tokenOne.symbol = conc.toString();
                tokenOne.type = Token.Type.SOMETHING;
                tokenOne.startPosition = startPosition;
                tokens.add(tokenOne);
                Token tokenTwo = new Token();
                tokenTwo.symbol = c;
                tokenTwo.type = Token.Type.SEPARATOR;
                tokenTwo.startPosition = i;
                tokens.add(tokenTwo);

                startPosition = i + 1;
                conc = new StringBuilder();
            } else {
                conc.append(c);
            }
        }
        if (!conc.toString().isEmpty()) {
            Token token = new Token();
            token.symbol = conc.toString();
            token.type = Token.Type.SOMETHING;
            token.startPosition = startPosition;
            tokens.add(token);
        }
        tokens.removeIf(t -> t.symbol.isEmpty() || t.symbol.equals(" "));
        for (String agg : aggregated) {
            tokens = replace(tokens, agg, Token.Type.SEPARATOR);
        }
        tokens.stream().forEach(t -> {
            if (isName(t.symbol)) {
                t.type = Token.Type.NAME;
            } else {
                switch (t.symbol) {
                    case "&&":
                    case "||":
                        t.type = Token.Type.LOGICAL;
                        break;
                    case ">":
                    case "<":
                    case ">=":
                    case "<=":
                    case "==":
                        t.type = Token.Type.RELATIONAL;
                        break;
                    case "(":
                        t.type = Token.Type.OPENING_PARENTHESIS;
                        break;
                    case ")":
                        t.type = Token.Type.CLOSING_PARENTHESIS;
                        break;
                }
            }
        });
        tokens = replaceOperation(tokens);
        return tokens;
    }

    ArrayList<Token> replace(ArrayList<Token> tokens, String forWhat, Token.Type type) {
        ArrayList<Token> result = new ArrayList<>();
        int i = 0;
        for (; i < tokens.size() - forWhat.length(); i++) {
            String phrase = String.join("", tokens.subList(i, i + forWhat.length()).stream().map(t -> t.symbol)
                    .collect(Collectors.toList()));
            if (phrase.equals(forWhat)) {
                Token newToken = new Token();
                newToken.symbol = phrase;
                newToken.type = type;
                newToken.startPosition = i;
                result.add(newToken);
                i += forWhat.length() - 1;
            } else {
                result.add(tokens.get(i));
            }
        }
        result.addAll(tokens.subList(i, tokens.size()));
        return result;
    }

    ArrayList<Token> replaceOperation(ArrayList<Token> tokens) {
        ArrayList<Token> result = new ArrayList<>();
        int i = 0;
        for (; i < tokens.size() - 1; i++) {
            Token t = tokens.get(i);
            if (t.type == Token.Type.NAME) {
                Token next = tokens.get(i + 1);
                if (next.symbol.equals("(")) {
                    int j = i + 2;
                    for (; j < tokens.size() && !tokens.get(j).symbol.equals(")"); j++);
                    if (j < tokens.size()) {
                        String phrase = String.join("",
                                tokens.subList(i, j + 1).stream().map(to -> to.symbol).collect(Collectors.toList()));
                        Token newToken = new Token();
                        newToken.symbol = phrase;
                        newToken.type = Token.Type.OPERATION;
                        newToken.startPosition = i;
                        result.add(newToken);
                        i = j;
                    } else {
                        result.add(t);
                    }
                }
                else {
                    result.add(t);
                }
            } else {
                result.add(t);
            }
        }
        result.addAll(tokens.subList(i, tokens.size()));
        return result;
    }

    boolean isName(String phrase) {
        String pattern = "[_a-zA-Z][.a-z0-9A-Z]*";
        return phrase.matches(pattern);
    }

    public static class Token {
        public String symbol;
        public Type type;
        public int startPosition;

        public enum Type {
            SEPARATOR,
            NAME,
            SOMETHING,
            OPERATION,
            RELATIONAL,
            LOGICAL,
            CLOSING_PARENTHESIS,
            OPENING_PARENTHESIS
        }
    }
}
