package uml.x.statemachine;

import org.junit.Test;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.assertFalse;

public class StateMachineTest {
    @Test
    public void simpleStateMachine() {
        StateMachine stateMachine = new StateMachine();

        State s1 = new State();
        State s2 = new State();

        Region r1 = new Region(s1);
        r1.addState(s2);

        Transition t1_s1_s2 = new Transition(1, s2);
        s1.addTransition(t1_s1_s2);

        stateMachine.addRegion(r1);

        Message m1 = new Message(null, new Event(1, null));
        stateMachine.entering(null);
        stateMachine.handle(m1);

        assertFalse(s1.isActive());
        assertTrue(s2.isActive());
    }
}
