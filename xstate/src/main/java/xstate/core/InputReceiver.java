package xstate.core;

import xstate.support.Input;

public interface InputReceiver {
    void onReceive(Input input);
}
