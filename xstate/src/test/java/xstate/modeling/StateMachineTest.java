package xstate.modeling;

import junit.framework.TestCase;
import xstate.modeling.build.Creator;
import xstate.support.Args;
import xstate.support.Guard;
import xstate.support.Input;
import xstate.support.extending.CodeSymbol;

import java.util.function.Function;

public class StateMachineTest extends TestCase {
    public void testSimple() {
        State whole = new State("State Whole");
        Region wholeRegion = new Region();
        State stateOne, stateTwo;
        stateOne = new State("State One");
        stateTwo = new State("State Two");
        FirstState wholeFirstState = new FirstState();
        Transition firstStateToStateOne = new Transition();
        Transition stateOneToStateTwo = new Transition();
        Terminator terminator = new Terminator();

        whole.addSubRegion(wholeRegion);
        wholeRegion.setJustOneStartingNode(wholeFirstState);
        wholeRegion.addChild(wholeFirstState);
        wholeRegion.addChild(stateOne);
        wholeRegion.addChild(stateTwo);
        wholeRegion.addChild(terminator);
        wholeFirstState.addOutgoingTransition(firstStateToStateOne);
        stateOne.addIncomingTransition(firstStateToStateOne);
        firstStateToStateOne.setSource(wholeFirstState);
        firstStateToStateOne.setDestination(stateOne);
        firstStateToStateOne.updateDiff();
        stateOne.addOutgoingTransition(stateOneToStateTwo);
        stateTwo.addIncomingTransition(stateOneToStateTwo);
        stateOneToStateTwo.addSymbol(new CodeSymbol(1));
        stateOneToStateTwo.addGuard(new Guard() {
            public boolean eval(Input input) {
                return ((int) input.getArgs().get(0)) == 10;
            }
        });
        stateOneToStateTwo.setSource(stateOne);
        stateOneToStateTwo.setDestination(stateTwo);
        stateOneToStateTwo.updateDiff();

        whole.onEntering(new Input(null, null), true);

        assertEquals(true, wholeRegion.isActive());
        assertEquals(true, whole.isActive());
        assertEquals(true, stateOne.isActive());
        assertEquals(false, stateTwo.isActive());

        Args args = new Args(1);
        args.set(0, 10);
        whole.onInput(new Input(new CodeSymbol(1), args));

        assertEquals(true, stateTwo.isActive());
        assertEquals(false, stateOne.isActive());
        assertEquals(true, whole.isActive());
        assertEquals(true, wholeRegion.isActive());
    }

    public void testOnExitingOnEntering() {
        String whole = "StateWhole";
        String wholeRegion = "WholeRegion";
        String wholeRegionFirstState = "WholeRegionFirstState";
        String deepStateOne = "StateDeepOne";
        String deepStateTwo = "StateDeepTwo";
        String deepStateOneRegionA = "DeepStateOneRegionA";
        String deepStateOneRegionB = "DeepStateOneRegionB";
        String deepStateTwoRegion = "DeepStateTwoRegion";
        String regionAFirstState = "RegionAFirstState";
        String regionBFirstState = "RegionBFirstState";
        String AState = "AState";
        String BStateOne = "BStateOne";
        String BStateTwo = "BStateTwo";
        String TRegionFirstState = "TRegionFirstState";
        String TStateA = "TStateA";
        String TStateARegion = "TStateARegion";
        String TStateARegionFirstState = "TStateARegionFirstState";
        String TStateARegionStateOne = "TStateARegionStateOne";

        String wholeRegionFirstStateToDeepStateOne = "transition1";
        String regionAFirstStateToAState = "transition2";
        String regionBFirstStateToBStateOne = "transition3";
        String BStateOneToBStateTwo = "transition4";
        String BStateTwoToTStateARegionStateOne = "transition5";
        String TRegionFirstStateToTStateA = "transition6";
        String TStateARegionFirstStateToTStateARegionStateOne = "transition7";

        String symbolA = "symbolA";
        String symbolB = "symbolB";

        Creator creator = new Creator();
        creator.createState(whole, whole);
        creator.createState(deepStateOne, deepStateOne);
        creator.createState(deepStateTwo, deepStateTwo);
        creator.createRegion(wholeRegion);
        creator.createRegion(deepStateOneRegionA);
        creator.createRegion(deepStateOneRegionB);
        creator.createRegion(deepStateTwoRegion);
        creator.createFirstState(wholeRegionFirstState);
        creator.createFirstState(regionAFirstState);
        creator.createFirstState(regionBFirstState);
        creator.createState(AState, AState);
        creator.createState(BStateOne, BStateOne);
        creator.createState(BStateTwo, BStateTwo);
        creator.createFirstState(TRegionFirstState);
        creator.createState(TStateA, TStateA);
        creator.createRegion(TStateARegion);
        creator.createFirstState(TStateARegionFirstState);
        creator.createState(TStateARegionStateOne, TStateARegionStateOne);
        creator.createTransition(wholeRegionFirstStateToDeepStateOne);
        creator.createTransition(regionAFirstStateToAState);
        creator.createTransition(regionBFirstStateToBStateOne);
        creator.createTransition(BStateOneToBStateTwo);
        creator.createTransition(BStateTwoToTStateARegionStateOne);
        creator.createTransition(TRegionFirstStateToTStateA);
        creator.createTransition(TStateARegionFirstStateToTStateARegionStateOne);
        creator.createCodeSymbol(symbolA, 1);
        creator.createCodeSymbol(symbolB, 2);

        creator.putSubRegionOnState(whole, wholeRegion);
        creator.putFirstStateOnRegion(wholeRegion, wholeRegionFirstState);
        creator.putStateOnRegion(wholeRegion, deepStateOne);
        creator.putStateOnRegion(wholeRegion, deepStateTwo);
        creator.putSubRegionOnState(deepStateOne, deepStateOneRegionA);
        creator.putSubRegionOnState(deepStateOne, deepStateOneRegionB);
        creator.putFirstStateOnRegion(deepStateOneRegionA, regionAFirstState);
        creator.putFirstStateOnRegion(deepStateOneRegionB, regionBFirstState);
        creator.putStateOnRegion(deepStateOneRegionA, AState);
        creator.putStateOnRegion(deepStateOneRegionB, BStateOne);
        creator.putStateOnRegion(deepStateOneRegionB, BStateTwo);
        creator.putSubRegionOnState(deepStateTwo, deepStateTwoRegion);
        creator.putFirstStateOnRegion(deepStateTwoRegion, TRegionFirstState);
        creator.putStateOnRegion(deepStateTwoRegion, TStateA);
        creator.putSubRegionOnState(TStateA, TStateARegion);
        creator.putFirstStateOnRegion(TStateARegion, TStateARegionFirstState);
        creator.putStateOnRegion(TStateARegion, TStateARegionStateOne);
        creator.putTransitionBetweenNodes(wholeRegionFirstStateToDeepStateOne, wholeRegionFirstState, deepStateOne);
        creator.putTransitionBetweenNodes(regionAFirstStateToAState, regionAFirstState, AState);
        creator.putTransitionBetweenNodes(regionBFirstStateToBStateOne, regionBFirstState, BStateOne);
        creator.putTransitionBetweenNodes(BStateOneToBStateTwo, BStateOne, BStateTwo); // need symbol
        creator.putTransitionBetweenNodes(BStateTwoToTStateARegionStateOne, BStateTwo, TStateARegionStateOne); // need symbol
        creator.putTransitionBetweenNodes(TRegionFirstStateToTStateA, TRegionFirstState, TStateA);
        creator.putTransitionBetweenNodes(TStateARegionFirstStateToTStateARegionStateOne, TStateARegionFirstState, TStateARegionStateOne);
        creator.putSymbolOnTransition(BStateOneToBStateTwo, symbolA);
        creator.putSymbolOnTransition(BStateTwoToTStateARegionStateOne, symbolB);

        State wholeState = (State) creator.getNode(whole);
        wholeState.onEntering(new Input(null, null), true);

        wholeState.onInput(new Input(creator.getSymbol(symbolA), null));
        wholeState.onInput(new Input(creator.getSymbol(symbolB), null));
    }

    public void testChoiceForSymbols() {
        String whole = "State Whole";
        String region = "Region";
        String firstState = "First State";
        String stateOne = "stateOne";
        String stateTwo = "stateTwo";
        String stateThree = "stateThree";
        String stateFour = "stateFour";
        String choice = "choice";
        String firstStateToStateOne = "firstStateToStateOne";
        String stateOneToChoice = "stateOneToChoice";
        String choiceToStateTwo = "choiceToStateTwo";
        String choiceToStateThree = "choiceToStateThree";
        String choiceToStateFour = "choiceToStateFour";
        String symbolA = "symbolA";
        String symbolB = "symbolB";
        String symbolC = "symbolC";

        Function<Void, Creator> smProducer = v -> {
            Creator creator = new Creator();
            creator.createState(whole, whole);
            creator.createState(stateOne, stateOne);
            creator.createState(stateTwo, stateTwo);
            creator.createState(stateThree, stateThree);
            creator.createState(stateFour, stateFour);
            creator.createRegion(region);
            creator.createFirstState(firstState);
            creator.createTransition(firstStateToStateOne);
            creator.createTransition(stateOneToChoice);
            creator.createTransition(choiceToStateTwo);
            creator.createTransition(choiceToStateThree);
            creator.createTransition(choiceToStateFour);
            creator.createChoice(choice);
            creator.createCodeSymbol(symbolA, 1);
            creator.createCodeSymbol(symbolB, 2);
            creator.createCodeSymbol(symbolC, 3);

            creator.putSubRegionOnState(whole, region);
            creator.putFirstStateOnRegion(region, firstState);
            creator.putStateOnRegion(region, stateOne);
            creator.putStateOnRegion(region, stateTwo);
            creator.putStateOnRegion(region, stateThree);
            creator.putStateOnRegion(region, stateFour);
            creator.putChoiceOnRegion(region, choice);
            creator.putTransitionBetweenNodes(firstStateToStateOne, firstState, stateOne);
            creator.putTransitionBetweenNodes(stateOneToChoice, stateOne, choice);
            creator.putTransitionBetweenNodes(choiceToStateTwo, choice, stateTwo);
            creator.putTransitionBetweenNodes(choiceToStateThree, choice, stateThree);
            creator.putTransitionBetweenNodes(choiceToStateFour, choice, stateFour);
            creator.putSymbolOnTransition(choiceToStateTwo, symbolA);
            creator.putSymbolOnTransition(choiceToStateThree, symbolB);
            creator.putSymbolOnTransition(choiceToStateFour, symbolC);

            return creator;
        };

        Creator creator = smProducer.apply(null);
        State sm = (State) creator.getNode(whole);
        sm.onEntering(new Input(null, null), true);
        sm.onInput(new Input(new CodeSymbol(1), null));
        assertEquals(true, creator.getNode(stateTwo).isActive());
        assertEquals(false, creator.getNode(stateThree).isActive());
        assertEquals(false, creator.getNode(stateFour).isActive());
        assertEquals(false, creator.getNode(stateOne).isActive());
        assertEquals(true, creator.getNode(whole).isActive());
        assertEquals(true, creator.getNode(region).isActive());

        creator = smProducer.apply(null);
        sm = (State) creator.getNode(whole);
        sm.onEntering();
        assertEquals(true, creator.getNode(stateOne).isActive());
        sm.onInput(new Input(new CodeSymbol(2), null));
        assertEquals(false, creator.getNode(stateTwo).isActive());
        assertEquals(true, creator.getNode(stateThree).isActive());
        assertEquals(false, creator.getNode(stateFour).isActive());
    }
}
