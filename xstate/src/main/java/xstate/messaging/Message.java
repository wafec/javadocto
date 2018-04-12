package xstate.messaging;

public class Message {
    public Object sender;
    public String title;
    public Object payload;

    public static Message create(Object sender, String title, Object payload) {
        Message message = new Message();
        message.sender = sender;
        message.title = title;
        message.payload = payload;
        return message;
    }
}
