export function Messagelist({messages, messageRef}) {
    return (
        <div className="messageList">
            {messages.map((msg, index) => (
                <div 
                    key={index}
                    className={msg.type === "sent" ? "messageBubble" : "agentMessageBubble"}
                >
                    {msg.text.split('\n').map((line, i) => (
                        <span key={i}>
                            {line}
                            <br />
                        </span>
                    ))}
                </div>
            ))}
            <div ref={messageRef} />
        </div>
    );
}
