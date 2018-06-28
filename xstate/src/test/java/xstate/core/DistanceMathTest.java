package xstate.core;

import junit.framework.TestCase;

public class DistanceMathTest extends TestCase {
    public void testComplex1() {
        int distance =
                xstate.core.DistanceMath.and(xstate.core.DistanceMath.greaterThan(783, 500),
                        xstate.core.DistanceMath.and(xstate.core.DistanceMath.lessThan(663, 100),
                                xstate.core.DistanceMath.greaterThan(663, 80)));
        assertEquals(distance, 564);
    }
}
