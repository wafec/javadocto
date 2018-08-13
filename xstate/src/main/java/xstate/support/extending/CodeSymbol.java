package xstate.support.extending;

import org.apache.log4j.Logger;
import xstate.support.Symbol;

public class CodeSymbol extends Symbol {
    static Logger log = Logger.getLogger(CodeSymbol.class);

    int number;

    public CodeSymbol(int number) {
        this.number = number;
    }

    public int getNumber() {
        return number;
    }

    @Override
    public boolean matchOther(Symbol other) {
        if (other instanceof CodeSymbol)
            return matchOther((CodeSymbol) other);
        return super.matchOther(other);
    }

    public boolean matchOther(CodeSymbol other) {
        return number == other.number;
    }
}
