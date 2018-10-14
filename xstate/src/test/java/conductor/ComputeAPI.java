package conductor;

public class ComputeAPI implements xstate.core.InputReceiver {
    final static String classifierId = "conductor.ComputeAPI";
    java.util.ArrayList<xstate.modeling.State> stateMachines = new java.util.ArrayList<>();


    public ComputeAPI() {
        initializeBehavior();
    }

    void initializeBehavior() {
        stateMachines.add(createComputeMachine());
        stateMachines.stream().forEach(sm -> sm.onEntering());
    }

    xstate.modeling.State createComputeMachine() {
        xstate.modeling.build.Creator creator = new xstate.modeling.build.Creator();
        creator.createState("_87t7gMf3Eei3kNLHQGb6pw", "ComputeMachine");
        creator.createState("_G1WTEMf4Eei3kNLHQGb6pw", "NoInstance");
        creator.createState("_JElx0Mf4Eei3kNLHQGb6pw", "InstanceReference");
        creator.createState("_dSOIwMf4Eei3kNLHQGb6pw", "ComputeReference");
        creator.createState("_eHxQsMf4Eei3kNLHQGb6pw", "ComputeAlternative");
        creator.createState("_ZK9YcMf4Eei3kNLHQGb6pw", "InstanceRunning");
        creator.createState("_abDuYMf4Eei3kNLHQGb6pw", "InstanceBuilding");
        creator.createState("_bcnSAMf4Eei3kNLHQGb6pw", "ImageReference");
        creator.createState("_cSkCkMf4Eei3kNLHQGb6pw", "ImageAlternative");
        creator.createState("_jb_jYMf4Eei3kNLHQGb6pw", "FlavorReference");
        creator.createState("_kMhocMf4Eei3kNLHQGb6pw", "FlavorAlternative");
        creator.createState("_petTwMf4Eei3kNLHQGb6pw", "InstanceShelved");
        creator.createState("_wlVWAMzLEeizl9GVJvL3HA", "FR_VerifyResize");
        creator.createState("_0p-3MMzLEeizl9GVJvL3HA", "FA_VerifyResize");
        creator.createFinalState("_-RUnEMf4Eei3kNLHQGb6pw");
        creator.createFirstState("_GLXh8Mf4Eei3kNLHQGb6pw", false);
        creator.createFirstState("_nCqIEMf4Eei3kNLHQGb6pw", true);
        creator.createFirstState("_YMhaQMf4Eei3kNLHQGb6pw", false);
        creator.createFirstState("_mBV1AMf4Eei3kNLHQGb6pw", true);
        creator.createFirstState("_nSnPoMf4Eei3kNLHQGb6pw", true);
        creator.createRegion("_9xlMgMf3Eei3kNLHQGb6pw");
        creator.createRegion("_TN8AYcf4Eei3kNLHQGb6pw");
        creator.createRegion("_UYgWEMf4Eei3kNLHQGb6pw");
        creator.createRegion("_VE_BkMf4Eei3kNLHQGb6pw");
        creator.createRegion("_WCJNYMf4Eei3kNLHQGb6pw");
        creator.createTransition("_HYXEEMf5Eei3kNLHQGb6pw");
        creator.createTransition("_96m6wMf5Eei3kNLHQGb6pw");
        creator.createTransition("_E_n1oMf6Eei3kNLHQGb6pw");
        creator.createTransition("_FnOoMMf6Eei3kNLHQGb6pw");
        creator.createTransition("_z5SKUMf6Eei3kNLHQGb6pw");
        creator.createTransition("_ACEw0MzMEeizl9GVJvL3HA");
        creator.createTransition("_DAfCsMzMEeizl9GVJvL3HA");
        creator.createTransition("_MSlgMMzMEeizl9GVJvL3HA");
        creator.createTransition("_NTOd0MzMEeizl9GVJvL3HA");
        creator.createTransition("_gd8zAMf6Eei3kNLHQGb6pw");
        creator.createTransition("_wfrKMMf6Eei3kNLHQGb6pw");
        creator.createTransition("_w_suEMf6Eei3kNLHQGb6pw");
        creator.createTransition("_hW83kMf6Eei3kNLHQGb6pw");
        creator.createTransition("_qjwlYMf6Eei3kNLHQGb6pw");
        creator.createTransition("_sFA8wMf6Eei3kNLHQGb6pw");
        creator.createTransition("_f_NBgMf6Eei3kNLHQGb6pw");
        creator.createTransition("_tQLIUMf6Eei3kNLHQGb6pw");
        creator.createTransition("_vxo_gMf6Eei3kNLHQGb6pw");
        creator.createTransition("_g3KkQMf6Eei3kNLHQGb6pw");
        creator.createTransition("_-J_N0MzLEeizl9GVJvL3HA");
        creator.createTransition("_JzZg8MzMEeizl9GVJvL3HA");
        creator.createCodeSymbol("_jh-vQMf7Eei3kNLHQGb6pw", conductor.START_INSTANCE.class.hashCode());
        creator.createCodeSymbol("_OpbpsMgUEei3kNLHQGb6pw", conductor.SHELVE_INSTANCE.class.hashCode());
        creator.createCodeSymbol("_UczWgMgUEei3kNLHQGb6pw", conductor.UNSHELVE_INSTANCE.class.hashCode());
        creator.createCodeSymbol("_KN0aAMgUEei3kNLHQGb6pw", conductor.DELETE_INSTANCE.class.hashCode());
        creator.createCodeSymbol("_aIgcQMzOEeizl9GVJvL3HA", conductor.CANCEL.class.hashCode());
        creator.createCodeSymbol("_eh9IwMzOEeizl9GVJvL3HA", conductor.CONFIRM.class.hashCode());
        creator.createCodeSymbol("_9rSGgMgTEei3kNLHQGb6pw", conductor.MIGRATE.class.hashCode());
        creator.createCodeSymbol("_ZD_ZgMgTEei3kNLHQGb6pw", conductor.BUILDING.class.hashCode());
        creator.createCodeSymbol("_eKh1gMgTEei3kNLHQGb6pw", conductor.BUILDED.class.hashCode());
        creator.createCodeSymbol("_vSNIIMgTEei3kNLHQGb6pw", conductor.REBUILD.class.hashCode());
        creator.createCodeSymbol("_DNPTMMgUEei3kNLHQGb6pw", conductor.RESIZE.class.hashCode());
        creator.recordOutput("_yNf7wMzNEeizl9GVJvL3HA", new xstate.support.Output() {
            @Override public void run(xstate.support.Input input) {
                conductor.MIGRATE event = xstate.support.Input.createFrom(input, conductor.MIGRATE.class);
                xstate.core.InputChannel.broadcastInput(xstate.support.Input.createTo(new conductor.BUILDING(), conductor.BUILDING.class));
            }
        });
        creator.recordOutput("_63oaUMzNEeizl9GVJvL3HA", new xstate.support.Output() {
            @Override public void run(xstate.support.Input input) {
                conductor.MIGRATE event = xstate.support.Input.createFrom(input, conductor.MIGRATE.class);
                xstate.core.InputChannel.broadcastInput(
                        xstate.support.Input.createTo(new conductor.BUILDING(), conductor.BUILDING.class));
            }
        });
        creator.recordOutput("_aApWMMzNEeizl9GVJvL3HA", new xstate.support.Output() {
            @Override public void run(xstate.support.Input input) {
                conductor.REBUILD event = xstate.support.Input.createFrom(input, conductor.REBUILD.class);
                xstate.core.InputChannel.broadcastInput(
                        xstate.support.Input.createTo(new conductor.BUILDING(), conductor.BUILDING.class));
            }
        });
        creator.recordOutput("_l_DB4MzNEeizl9GVJvL3HA", new xstate.support.Output() {
            @Override public void run(xstate.support.Input input) {
                conductor.REBUILD event = xstate.support.Input.createFrom(input, conductor.REBUILD.class);
                xstate.core.InputChannel.broadcastInput(
                        xstate.support.Input.createTo(new conductor.BUILDING(), conductor.BUILDING.class));
            }
        });
        creator.recordOutput("_3axVQMgUEei3kNLHQGb6pw", new xstate.support.Output() {
            @Override public void run(xstate.support.Input input) {
                xstate.core.InputChannel.broadcastInput(
                        xstate.support.Input.createTo(new conductor.BUILDED(), conductor.BUILDED.class));
            }
        });
        creator.recordOutput("_ffImEMgVEei3kNLHQGb6pw", new xstate.support.Output() {
            @Override public void run(xstate.support.Input input) {
                xstate.core.InputChannel.broadcastInput(
                        xstate.support.Input.createTo(new conductor.BUILDED(), conductor.BUILDED.class));
            }
        });
        creator.recordOutput("_jZ8rQMgUEei3kNLHQGb6pw", new xstate.support.Output() {
            @Override public void run(xstate.support.Input input) {
                xstate.core.InputChannel.broadcastInput(
                        xstate.support.Input.createTo(new conductor.BUILDED(), conductor.BUILDED.class));
            }
        });
        creator.recordOutput("_QR4YwMgVEei3kNLHQGb6pw", new xstate.support.Output() {
            @Override public void run(xstate.support.Input input) {
                xstate.core.InputChannel.broadcastInput(
                        xstate.support.Input.createTo(new conductor.BUILDED(), conductor.BUILDED.class));
            }
        });
        creator.recordOutput("_CdLSwMgVEei3kNLHQGb6pw", new xstate.support.Output() {
            @Override public void run(xstate.support.Input input) {
                xstate.core.InputChannel.broadcastInput(
                        xstate.support.Input.createTo(new conductor.BUILDED(), conductor.BUILDED.class));
            }
        });
        creator.recordOutput("_pOx7MMgVEei3kNLHQGb6pw", new xstate.support.Output() {
            @Override public void run(xstate.support.Input input) {
                xstate.core.InputChannel.broadcastInput(
                        xstate.support.Input.createTo(new conductor.BUILDED(), conductor.BUILDED.class));
            }
        });
        creator.putStateOnRegion("_9xlMgMf3Eei3kNLHQGb6pw", "_G1WTEMf4Eei3kNLHQGb6pw");
        creator.putStateOnRegion("_9xlMgMf3Eei3kNLHQGb6pw", "_JElx0Mf4Eei3kNLHQGb6pw");
        creator.putStateOnRegion("_TN8AYcf4Eei3kNLHQGb6pw", "_dSOIwMf4Eei3kNLHQGb6pw");
        creator.putStateOnRegion("_TN8AYcf4Eei3kNLHQGb6pw", "_eHxQsMf4Eei3kNLHQGb6pw");
        creator.putStateOnRegion("_UYgWEMf4Eei3kNLHQGb6pw", "_ZK9YcMf4Eei3kNLHQGb6pw");
        creator.putStateOnRegion("_UYgWEMf4Eei3kNLHQGb6pw", "_abDuYMf4Eei3kNLHQGb6pw");
        creator.putStateOnRegion("_VE_BkMf4Eei3kNLHQGb6pw", "_bcnSAMf4Eei3kNLHQGb6pw");
        creator.putStateOnRegion("_VE_BkMf4Eei3kNLHQGb6pw", "_cSkCkMf4Eei3kNLHQGb6pw");
        creator.putStateOnRegion("_WCJNYMf4Eei3kNLHQGb6pw", "_jb_jYMf4Eei3kNLHQGb6pw");
        creator.putStateOnRegion("_WCJNYMf4Eei3kNLHQGb6pw", "_kMhocMf4Eei3kNLHQGb6pw");
        creator.putStateOnRegion("_9xlMgMf3Eei3kNLHQGb6pw", "_petTwMf4Eei3kNLHQGb6pw");
        creator.putStateOnRegion("_9xlMgMf3Eei3kNLHQGb6pw", "_wlVWAMzLEeizl9GVJvL3HA");
        creator.putStateOnRegion("_9xlMgMf3Eei3kNLHQGb6pw", "_0p-3MMzLEeizl9GVJvL3HA");
        creator.putFinalStateOnRegion("_9xlMgMf3Eei3kNLHQGb6pw", "_-RUnEMf4Eei3kNLHQGb6pw");
        creator.putSubRegionOnState("_87t7gMf3Eei3kNLHQGb6pw", "_9xlMgMf3Eei3kNLHQGb6pw");
        creator.putSubRegionOnState("_JElx0Mf4Eei3kNLHQGb6pw", "_TN8AYcf4Eei3kNLHQGb6pw");
        creator.putSubRegionOnState("_JElx0Mf4Eei3kNLHQGb6pw", "_UYgWEMf4Eei3kNLHQGb6pw");
        creator.putSubRegionOnState("_JElx0Mf4Eei3kNLHQGb6pw", "_VE_BkMf4Eei3kNLHQGb6pw");
        creator.putSubRegionOnState("_JElx0Mf4Eei3kNLHQGb6pw", "_WCJNYMf4Eei3kNLHQGb6pw");
        creator.putFirstStateOnRegion("_9xlMgMf3Eei3kNLHQGb6pw", "_GLXh8Mf4Eei3kNLHQGb6pw");
        creator.putFirstStateOnRegion("_TN8AYcf4Eei3kNLHQGb6pw", "_nCqIEMf4Eei3kNLHQGb6pw");
        creator.putFirstStateOnRegion("_UYgWEMf4Eei3kNLHQGb6pw", "_YMhaQMf4Eei3kNLHQGb6pw");
        creator.putFirstStateOnRegion("_VE_BkMf4Eei3kNLHQGb6pw", "_mBV1AMf4Eei3kNLHQGb6pw");
        creator.putFirstStateOnRegion("_WCJNYMf4Eei3kNLHQGb6pw", "_nSnPoMf4Eei3kNLHQGb6pw");
        creator.putTransitionBetweenNodes("_HYXEEMf5Eei3kNLHQGb6pw", "_GLXh8Mf4Eei3kNLHQGb6pw", "_G1WTEMf4Eei3kNLHQGb6pw");
        creator.putTransitionBetweenNodes("_96m6wMf5Eei3kNLHQGb6pw", "_G1WTEMf4Eei3kNLHQGb6pw", "_JElx0Mf4Eei3kNLHQGb6pw");
        creator.putTransitionBetweenNodes("_E_n1oMf6Eei3kNLHQGb6pw", "_JElx0Mf4Eei3kNLHQGb6pw", "_petTwMf4Eei3kNLHQGb6pw");
        creator.putTransitionBetweenNodes("_FnOoMMf6Eei3kNLHQGb6pw", "_petTwMf4Eei3kNLHQGb6pw", "_JElx0Mf4Eei3kNLHQGb6pw");
        creator.putTransitionBetweenNodes("_z5SKUMf6Eei3kNLHQGb6pw", "_JElx0Mf4Eei3kNLHQGb6pw", "_-RUnEMf4Eei3kNLHQGb6pw");
        creator.putTransitionBetweenNodes("_ACEw0MzMEeizl9GVJvL3HA", "_wlVWAMzLEeizl9GVJvL3HA", "_jb_jYMf4Eei3kNLHQGb6pw");
        creator.putTransitionBetweenNodes("_DAfCsMzMEeizl9GVJvL3HA", "_wlVWAMzLEeizl9GVJvL3HA", "_kMhocMf4Eei3kNLHQGb6pw");
        creator.putTransitionBetweenNodes("_MSlgMMzMEeizl9GVJvL3HA", "_0p-3MMzLEeizl9GVJvL3HA", "_kMhocMf4Eei3kNLHQGb6pw");
        creator.putTransitionBetweenNodes("_NTOd0MzMEeizl9GVJvL3HA", "_0p-3MMzLEeizl9GVJvL3HA", "_jb_jYMf4Eei3kNLHQGb6pw");
        creator.putTransitionBetweenNodes("_gd8zAMf6Eei3kNLHQGb6pw", "_nCqIEMf4Eei3kNLHQGb6pw", "_dSOIwMf4Eei3kNLHQGb6pw");
        creator.putTransitionBetweenNodes("_wfrKMMf6Eei3kNLHQGb6pw", "_dSOIwMf4Eei3kNLHQGb6pw", "_eHxQsMf4Eei3kNLHQGb6pw");
        creator.putTransitionBetweenNodes("_w_suEMf6Eei3kNLHQGb6pw", "_eHxQsMf4Eei3kNLHQGb6pw", "_dSOIwMf4Eei3kNLHQGb6pw");
        creator.putTransitionBetweenNodes("_hW83kMf6Eei3kNLHQGb6pw", "_YMhaQMf4Eei3kNLHQGb6pw", "_ZK9YcMf4Eei3kNLHQGb6pw");
        creator.putTransitionBetweenNodes("_qjwlYMf6Eei3kNLHQGb6pw", "_ZK9YcMf4Eei3kNLHQGb6pw", "_abDuYMf4Eei3kNLHQGb6pw");
        creator.putTransitionBetweenNodes("_sFA8wMf6Eei3kNLHQGb6pw", "_abDuYMf4Eei3kNLHQGb6pw", "_ZK9YcMf4Eei3kNLHQGb6pw");
        creator.putTransitionBetweenNodes("_f_NBgMf6Eei3kNLHQGb6pw", "_mBV1AMf4Eei3kNLHQGb6pw", "_bcnSAMf4Eei3kNLHQGb6pw");
        creator.putTransitionBetweenNodes("_tQLIUMf6Eei3kNLHQGb6pw", "_bcnSAMf4Eei3kNLHQGb6pw", "_cSkCkMf4Eei3kNLHQGb6pw");
        creator.putTransitionBetweenNodes("_vxo_gMf6Eei3kNLHQGb6pw", "_cSkCkMf4Eei3kNLHQGb6pw", "_bcnSAMf4Eei3kNLHQGb6pw");
        creator.putTransitionBetweenNodes("_g3KkQMf6Eei3kNLHQGb6pw", "_nSnPoMf4Eei3kNLHQGb6pw", "_jb_jYMf4Eei3kNLHQGb6pw");
        creator.putTransitionBetweenNodes("_-J_N0MzLEeizl9GVJvL3HA", "_jb_jYMf4Eei3kNLHQGb6pw", "_wlVWAMzLEeizl9GVJvL3HA");
        creator.putTransitionBetweenNodes("_JzZg8MzMEeizl9GVJvL3HA", "_kMhocMf4Eei3kNLHQGb6pw", "_0p-3MMzLEeizl9GVJvL3HA");
        creator.putSymbolOnTransition("_96m6wMf5Eei3kNLHQGb6pw", "_jh-vQMf7Eei3kNLHQGb6pw");
        creator.putSymbolOnTransition("_E_n1oMf6Eei3kNLHQGb6pw", "_OpbpsMgUEei3kNLHQGb6pw");
        creator.putSymbolOnTransition("_FnOoMMf6Eei3kNLHQGb6pw", "_UczWgMgUEei3kNLHQGb6pw");
        creator.putSymbolOnTransition("_z5SKUMf6Eei3kNLHQGb6pw", "_KN0aAMgUEei3kNLHQGb6pw");
        creator.putSymbolOnTransition("_ACEw0MzMEeizl9GVJvL3HA", "_aIgcQMzOEeizl9GVJvL3HA");
        creator.putSymbolOnTransition("_DAfCsMzMEeizl9GVJvL3HA", "_eh9IwMzOEeizl9GVJvL3HA");
        creator.putSymbolOnTransition("_MSlgMMzMEeizl9GVJvL3HA", "_aIgcQMzOEeizl9GVJvL3HA");
        creator.putSymbolOnTransition("_NTOd0MzMEeizl9GVJvL3HA", "_eh9IwMzOEeizl9GVJvL3HA");
        creator.putSymbolOnTransition("_wfrKMMf6Eei3kNLHQGb6pw", "_9rSGgMgTEei3kNLHQGb6pw");
        creator.putSymbolOnTransition("_w_suEMf6Eei3kNLHQGb6pw", "_9rSGgMgTEei3kNLHQGb6pw");
        creator.putSymbolOnTransition("_qjwlYMf6Eei3kNLHQGb6pw", "_ZD_ZgMgTEei3kNLHQGb6pw");
        creator.putSymbolOnTransition("_sFA8wMf6Eei3kNLHQGb6pw", "_eKh1gMgTEei3kNLHQGb6pw");
        creator.putSymbolOnTransition("_tQLIUMf6Eei3kNLHQGb6pw", "_vSNIIMgTEei3kNLHQGb6pw");
        creator.putSymbolOnTransition("_vxo_gMf6Eei3kNLHQGb6pw", "_vSNIIMgTEei3kNLHQGb6pw");
        creator.putSymbolOnTransition("_-J_N0MzLEeizl9GVJvL3HA", "_DNPTMMgUEei3kNLHQGb6pw");
        creator.putSymbolOnTransition("_JzZg8MzMEeizl9GVJvL3HA", "_DNPTMMgUEei3kNLHQGb6pw");
        creator.putOutputOnTransition("_wfrKMMf6Eei3kNLHQGb6pw", "_yNf7wMzNEeizl9GVJvL3HA");
        creator.putOutputOnTransition("_w_suEMf6Eei3kNLHQGb6pw", "_63oaUMzNEeizl9GVJvL3HA");
        creator.putOutputOnTransition("_tQLIUMf6Eei3kNLHQGb6pw", "_aApWMMzNEeizl9GVJvL3HA");
        creator.putOutputOnTransition("_vxo_gMf6Eei3kNLHQGb6pw", "_l_DB4MzNEeizl9GVJvL3HA");
        creator.putOutputOnStateForEntering("_dSOIwMf4Eei3kNLHQGb6pw", "_3axVQMgUEei3kNLHQGb6pw");
        creator.putOutputOnStateForEntering("_eHxQsMf4Eei3kNLHQGb6pw", "_ffImEMgVEei3kNLHQGb6pw");
        creator.putOutputOnStateForEntering("_bcnSAMf4Eei3kNLHQGb6pw", "_jZ8rQMgUEei3kNLHQGb6pw");
        creator.putOutputOnStateForEntering("_cSkCkMf4Eei3kNLHQGb6pw", "_QR4YwMgVEei3kNLHQGb6pw");
        creator.putOutputOnStateForEntering("_jb_jYMf4Eei3kNLHQGb6pw", "_CdLSwMgVEei3kNLHQGb6pw");
        creator.putOutputOnStateForEntering("_kMhocMf4Eei3kNLHQGb6pw", "_pOx7MMgVEei3kNLHQGb6pw");
        creator.setClassifierId(classifierId);
        return (xstate.modeling.State) creator.getNode("_87t7gMf3Eei3kNLHQGb6pw");
    }

    @Override public void onReceive(xstate.support.Input input) {
        stateMachines.stream().forEach(sm -> sm.onInput(input));
    }
}
