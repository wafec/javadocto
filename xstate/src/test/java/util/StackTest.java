package util;

import junit.framework.TestCase;
import xstate.support.Input;

public class StackTest extends TestCase {
    public void testFull() {
        Stack stack = new Stack(10);
        Push push = new Push();
        Pop pop = new Pop();
        assertEquals(0, (int) stack.size);
        stack.onReceive(Input.createTo(push, Push.class));
        assertEquals(1, (int) stack.size);
        stack.onReceive(Input.createTo(push, Push.class));
        assertEquals(2, (int) stack.size);
        stack.onReceive(Input.createTo(pop, Pop.class));
        assertEquals(1, (int) stack.size);
    }
}
