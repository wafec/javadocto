package conductor;

import junit.framework.TestCase;
import xstate.core.InputChannel;
import xstate.messaging.Message;
import xstate.messaging.MessageBroker;
import xstate.messaging.Subscriber;
import xstate.messaging.Subscription;
import xstate.support.Input;
import xstate.support.messaging.ArrowMessage;

import java.util.ArrayList;

public class ComputeAPITest extends TestCase {

    class ComputeSubscriber implements Subscriber {
        ArrayList<ArrowMessage> arrowMessages = new ArrayList<>();

        @Override
        public void accept(Message message) {
            if (message instanceof ArrowMessage) {
                ArrowMessage arrowMessage = (ArrowMessage) message;
                if (arrowMessage.getState() == ArrowMessage.States.TRANSITED) {
                    arrowMessages.add((ArrowMessage) message);
                }
            }
        }
    }

    public void testBasic() {
        ComputeAPI api = new ComputeAPI();
        Subscription subs = new Subscription();
        ComputeSubscriber computeSubscriber = new ComputeSubscriber();
        subs.subscriber = computeSubscriber;
        MessageBroker.getSingleton().addSubscription(subs);
        api.onReceive(Input.createTo(new START_INSTANCE(), START_INSTANCE.class));
        api.onReceive(Input.createTo(new MIGRATE(), MIGRATE.class));
        api.onReceive(Input.createTo(new RESIZE(), RESIZE.class));
        api.onReceive(Input.createTo(new SHELVE_INSTANCE(), SHELVE_INSTANCE.class));
        api.onReceive(Input.createTo(new UNSHELVE_INSTANCE(), UNSHELVE_INSTANCE.class));
        api.onReceive(Input.createTo(new REBUILD(), REBUILD.class));
        computeSubscriber.arrowMessages.clear();
        api.onReceive(Input.createTo(new DELETE_INSTANCE(), DELETE_INSTANCE.class));
    }

    public void testBroadcast() {
        ComputeAPI api = new ComputeAPI();
        Subscription subs = new Subscription();
        ComputeSubscriber subscriber = new ComputeSubscriber();
        subs.subscriber = subscriber;
        MessageBroker.getSingleton().addSubscription(subs);
        InputChannel.register(api);
        api.onReceive(Input.createTo(new START_INSTANCE(), START_INSTANCE.class));
        api.onReceive(Input.createTo(new MIGRATE(), MIGRATE.class));
        InputChannel.unregister(api);
    }

    public void testCompositeState() {
        ComputeAPI api = new ComputeAPI();
        Subscription subs = new Subscription();
        ComputeSubscriber subscriber = new ComputeSubscriber();
        subs.subscriber = subscriber;
        MessageBroker.getSingleton().addSubscription(subs);
        InputChannel.register(api);
        api.onReceive(Input.createTo(new START_INSTANCE(), START_INSTANCE.class));
        api.onReceive(Input.createTo(new MIGRATE(), MIGRATE.class));
        api.onReceive(Input.createTo(new RESIZE(), RESIZE.class));
        api.onReceive(Input.createTo(new CONFIRM(), CONFIRM.class));
        InputChannel.unregister(api);
    }
}
