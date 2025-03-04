export function Messagelist({messages, messageRef}) {
    return (
        <div className = "messageList">
            {messages.map((msg, index) => (
                <div 
                    key = {index}
                    className={msg.type === "sent" ? "messageBubble" : "agentMessageBubble"}
                >
                    {msg.text}
                </div>
            ))}
            <div ref = {messageRef} />
        </div>
    );
}