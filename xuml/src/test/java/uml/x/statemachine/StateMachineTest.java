package uml.x.statemachine;

import org.junit.Test;

import java.util.ArrayList;
import java.util.stream.Collectors;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.assertFalse;

public class StateMachineTest {
    @Test
    public void testSimpleStateMachine() {
        StateMachine stateMachine = new StateMachine("StateMachine");

        State s1 = new State("State 1");
        State s2 = new State("State 2");

        Region r1 = new Region(s1);
        r1.addState(s2);

        Transition t1_s1_s2 = new Transition(1, 1, s2);
        s1.addTransition(t1_s1_s2);

        stateMachine.addRegion(r1);

        Tracker tracker = new Tracker();
        Message m1 = new Message(null, new Event(1, null), tracker);
        stateMachine.entering(new Message(null, null, tracker));
        stateMachine.handle(m1);

        assertFalse(s1.isActive());
        assertTrue(s2.isActive());
        ArrayList<TrackingLog> sequence = tracker.filter(State.EnteredLog.class);
        assertEquals(s1.getName(), sequence.get(1).getData().toString());
        assertEquals(s2.getName(), sequence.get(2).getData().toString());
    }

    @Test
    public void testEnsureExiting() {
        StateMachine stateMachine = new StateMachine("StateMachine");

        State s1 = new State("State 1");
        State s2 = new State("State 2");
        State s3 = new State("State 3");

        Region r1 = new Region(s1);
        r1.addState(s2);
        Region r2 = new Region(s3);
        s1.addRegion(r2);

        Transition t1 = new Transition(1, 1, s2);
        s1.addTransition(t1);

        stateMachine.addRegion(r1);

        Tracker tracker = new Tracker();
        Message m = new Message(null, new Event(1, null), tracker);
        stateMachine.entering(new Message(null, null, tracker));
        stateMachine.handle(m);

        ArrayList<TrackingLog> sequence = tracker.filter(State.EnteredLog.class);
        assertEquals(stateMachine.getName(), sequence.get(0).getData());
        assertEquals(s1.getName(), sequence.get(1).getData());
        assertEquals(s3.getName(), sequence.get(2).getData());
        assertEquals(s2.getName(), sequence.get(3).getData());

        sequence = tracker.filter(State.ExitedLog.class);
        assertEquals(s3.getName(), sequence.get(0).getData());
        assertEquals(s1.getName(), sequence.get(1).getData());
    }

    @Test
    public void testHistory() {
        StateMachine stateMachine = new StateMachine("StateMachine");
        State s1 = new State("State 1");
        State a1 = new State("State A1");
        State b1 = new State("State B1");
        State s2 = new State("State 2");

        Transition t1 = new Transition(1, 1, s2);
        Transition t2 = new Transition(2, 1, s1);

        s1.addTransition(t1);
        s2.addTransition(t2);

        Region r1 = new Region(s1);
        r1.addState(s2);

        Region r2 = new Region(a1, true);
        r2.addState(b1);

        Transition t3 = new Transition(3, 2, b1);
        a1.addTransition(t3);

        stateMachine.addRegion(r1);
        s1.addRegion(r2);

        Tracker tracker = new Tracker();
        stateMachine.entering(new Message(null, null, tracker));
        stateMachine.handle(new Message(null, new Event(1, null), tracker));
        stateMachine.handle(new Message(null, new Event(2, null), tracker));
        stateMachine.handle(new Message(null, new Event(1, null), tracker));

        assertTrue("S1 must be active", s1.isActive());
        assertTrue("B1 must be active", b1.isActive());
    }
}
