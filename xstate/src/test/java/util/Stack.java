package util;

public class Stack {
    java.util.ArrayList<xstate.modeling.State> stateMachines = new java.util.ArrayList<>();

    public java.lang.Integer size;
    public java.lang.Integer capacity;

    public Stack() {
        initializeBehavior();
    }

    void initializeBehavior() {
        stateMachines.add(createstackProtocol());
        stateMachines.stream().forEach(sm -> sm.onEntering());
    }

    xstate.modeling.State createstackProtocol() {
        xstate.modeling.build.Creator creator = new xstate.modeling.build.Creator();
        creator.createState("_2G6f0D3fEeiVCInSg7lKsg", "stackProtocol");
        creator.createState("_8mqxgD3fEeiVCInSg7lKsg", "Empty");
        creator.createState("_9t3DED3fEeiVCInSg7lKsg", "Normal");
        creator.createState("_-hv-ID3fEeiVCInSg7lKsg", "Full");
        creator.createState("___si0D3fEeiVCInSg7lKsg", "Error");
        creator.createFirstState("_64AQQD3fEeiVCInSg7lKsg");
        creator.createRegion("_5Vrh4D3fEeiVCInSg7lKsg");
        creator.createTransition("_B_3q0D3gEeiVCInSg7lKsg");
        creator.createTransition("_C8NXQD3gEeiVCInSg7lKsg");
        creator.createTransition("_DengwD3gEeiVCInSg7lKsg");
        creator.createTransition("_EZ5dQD3gEeiVCInSg7lKsg");
        creator.createTransition("_FCMMUD3gEeiVCInSg7lKsg");
        creator.createTransition("_FyYTID3gEeiVCInSg7lKsg");
        creator.createTransition("_GXfLUD3gEeiVCInSg7lKsg");
        creator.createTransition("_QOd3gD3gEeiVCInSg7lKsg");
        creator.createTransition("_VA_LUD3gEeiVCInSg7lKsg");
        creator.createCodeSymbol("_61ZLsD3gEeiVCInSg7lKsg", util.Push.class.hashCode());
        creator.createCodeSymbol("_-Y8K8D3gEeiVCInSg7lKsg", util.Pop.class.hashCode());
        creator.recordGuard("_MLGTQD3hEeiVCInSg7lKsg", new xstate.support.Guard() {
            @Override public int evalInteger(xstate.support.Input input) {
                util.Pop event = xstate.support.Input.createFrom(input, util.Pop.class);
                return xstate.core.DistanceMath.equalThan(size, 1);
            }
        });
        creator.recordGuard("_oPPTcD3hEeiVCInSg7lKsg", new xstate.support.Guard() {
            @Override public int evalInteger(xstate.support.Input input) {
                util.Push event = xstate.support.Input.createFrom(input, util.Push.class);
                return xstate.core.DistanceMath.equalThan(size, capacity);
            }
        });
        creator.recordGuard("_gDey8D3hEeiVCInSg7lKsg", new xstate.support.Guard() {
            @Override public int evalInteger(xstate.support.Input input) {
                util.Push event = xstate.support.Input.createFrom(input, util.Push.class);
                return xstate.core.DistanceMath.lessThan(size, capacity);
            }
        });
        creator.recordGuard("_Y6VmAD3hEeiVCInSg7lKsg", new xstate.support.Guard() {
            @Override public int evalInteger(xstate.support.Input input) {
                util.Pop event = xstate.support.Input.createFrom(input, util.Pop.class);
                return xstate.core.DistanceMath.greaterThan(size, 1);
            }
        });
        creator.recordOutput("_H0oM0D3iEeiVCInSg7lKsg", new xstate.support.Output() {
            @Override public void run(xstate.support.Input input) {
                util.Push event = xstate.support.Input.createFrom(input, util.Push.class);
                size++;
            }
        });
        creator.recordOutput("_F7SsoD3iEeiVCInSg7lKsg", new xstate.support.Output() {
            @Override public void run(xstate.support.Input input) {
                util.Pop event = xstate.support.Input.createFrom(input, util.Pop.class);
                size--;
            }
        });
        creator.recordOutput("_ODVKwD3iEeiVCInSg7lKsg", new xstate.support.Output() {
            @Override public void run(xstate.support.Input input) {
                util.Push event = xstate.support.Input.createFrom(input, util.Push.class);
                size++;
            }
        });
        creator.recordOutput("_Mt0wYD3iEeiVCInSg7lKsg", new xstate.support.Output() {
            @Override public void run(xstate.support.Input input) {
                util.Pop event = xstate.support.Input.createFrom(input, util.Pop.class);
                size--;
            }
        });
        creator.recordOutput("_LLfa8D3iEeiVCInSg7lKsg", new xstate.support.Output() {
            @Override public void run(xstate.support.Input input) {
                util.Push event = xstate.support.Input.createFrom(input, util.Push.class);
                size++;
            }
        });
        creator.recordOutput("_Jul_ID3iEeiVCInSg7lKsg", new xstate.support.Output() {
            @Override public void run(xstate.support.Input input) {
                util.Pop event = xstate.support.Input.createFrom(input, util.Pop.class);
                size--;
            }
        });
        creator.putStateOnRegion("_5Vrh4D3fEeiVCInSg7lKsg", "_8mqxgD3fEeiVCInSg7lKsg");
        creator.putStateOnRegion("_5Vrh4D3fEeiVCInSg7lKsg", "_9t3DED3fEeiVCInSg7lKsg");
        creator.putStateOnRegion("_5Vrh4D3fEeiVCInSg7lKsg", "_-hv-ID3fEeiVCInSg7lKsg");
        creator.putStateOnRegion("_5Vrh4D3fEeiVCInSg7lKsg", "___si0D3fEeiVCInSg7lKsg");
        creator.putSubRegionOnState("_2G6f0D3fEeiVCInSg7lKsg", "_5Vrh4D3fEeiVCInSg7lKsg");
        creator.putFirstStateOnRegion("_5Vrh4D3fEeiVCInSg7lKsg", "_64AQQD3fEeiVCInSg7lKsg");
        creator.putTransitionBetweenNodes("_B_3q0D3gEeiVCInSg7lKsg", "_64AQQD3fEeiVCInSg7lKsg", "_8mqxgD3fEeiVCInSg7lKsg");
        creator.putTransitionBetweenNodes("_C8NXQD3gEeiVCInSg7lKsg", "_8mqxgD3fEeiVCInSg7lKsg", "_9t3DED3fEeiVCInSg7lKsg");
        creator.putTransitionBetweenNodes("_DengwD3gEeiVCInSg7lKsg", "_9t3DED3fEeiVCInSg7lKsg", "_8mqxgD3fEeiVCInSg7lKsg");
        creator.putTransitionBetweenNodes("_EZ5dQD3gEeiVCInSg7lKsg", "_9t3DED3fEeiVCInSg7lKsg", "_-hv-ID3fEeiVCInSg7lKsg");
        creator.putTransitionBetweenNodes("_FCMMUD3gEeiVCInSg7lKsg", "_-hv-ID3fEeiVCInSg7lKsg", "_9t3DED3fEeiVCInSg7lKsg");
        creator.putTransitionBetweenNodes("_FyYTID3gEeiVCInSg7lKsg", "_-hv-ID3fEeiVCInSg7lKsg", "___si0D3fEeiVCInSg7lKsg");
        creator.putTransitionBetweenNodes("_GXfLUD3gEeiVCInSg7lKsg", "_8mqxgD3fEeiVCInSg7lKsg", "___si0D3fEeiVCInSg7lKsg");
        creator.putTransitionBetweenNodes("_QOd3gD3gEeiVCInSg7lKsg", "_9t3DED3fEeiVCInSg7lKsg", "_9t3DED3fEeiVCInSg7lKsg");
        creator.putTransitionBetweenNodes("_VA_LUD3gEeiVCInSg7lKsg", "_9t3DED3fEeiVCInSg7lKsg", "_9t3DED3fEeiVCInSg7lKsg");
        creator.putSymbolOnTransition("_C8NXQD3gEeiVCInSg7lKsg", "_61ZLsD3gEeiVCInSg7lKsg");
        creator.putSymbolOnTransition("_DengwD3gEeiVCInSg7lKsg", "_-Y8K8D3gEeiVCInSg7lKsg");
        creator.putSymbolOnTransition("_EZ5dQD3gEeiVCInSg7lKsg", "_61ZLsD3gEeiVCInSg7lKsg");
        creator.putSymbolOnTransition("_FCMMUD3gEeiVCInSg7lKsg", "_-Y8K8D3gEeiVCInSg7lKsg");
        creator.putSymbolOnTransition("_FyYTID3gEeiVCInSg7lKsg", "_61ZLsD3gEeiVCInSg7lKsg");
        creator.putSymbolOnTransition("_GXfLUD3gEeiVCInSg7lKsg", "_-Y8K8D3gEeiVCInSg7lKsg");
        creator.putSymbolOnTransition("_QOd3gD3gEeiVCInSg7lKsg", "_61ZLsD3gEeiVCInSg7lKsg");
        creator.putSymbolOnTransition("_VA_LUD3gEeiVCInSg7lKsg", "_-Y8K8D3gEeiVCInSg7lKsg");
        creator.putGuardOnTransition("_DengwD3gEeiVCInSg7lKsg", "_MLGTQD3hEeiVCInSg7lKsg");
        creator.putGuardOnTransition("_EZ5dQD3gEeiVCInSg7lKsg", "_oPPTcD3hEeiVCInSg7lKsg");
        creator.putGuardOnTransition("_QOd3gD3gEeiVCInSg7lKsg", "_gDey8D3hEeiVCInSg7lKsg");
        creator.putGuardOnTransition("_VA_LUD3gEeiVCInSg7lKsg", "_Y6VmAD3hEeiVCInSg7lKsg");
        creator.putOutputOnTransition("_C8NXQD3gEeiVCInSg7lKsg", "_H0oM0D3iEeiVCInSg7lKsg");
        creator.putOutputOnTransition("_DengwD3gEeiVCInSg7lKsg", "_F7SsoD3iEeiVCInSg7lKsg");
        creator.putOutputOnTransition("_EZ5dQD3gEeiVCInSg7lKsg", "_ODVKwD3iEeiVCInSg7lKsg");
        creator.putOutputOnTransition("_FCMMUD3gEeiVCInSg7lKsg", "_Mt0wYD3iEeiVCInSg7lKsg");
        creator.putOutputOnTransition("_QOd3gD3gEeiVCInSg7lKsg", "_LLfa8D3iEeiVCInSg7lKsg");
        creator.putOutputOnTransition("_VA_LUD3gEeiVCInSg7lKsg", "_Jul_ID3iEeiVCInSg7lKsg");
        return (xstate.modeling.State) creator.getNode("_2G6f0D3fEeiVCInSg7lKsg");
    }

    public void onReceive(xstate.support.Input input) {
        stateMachines.stream().forEach(sm -> sm.onInput(input));
    }
}