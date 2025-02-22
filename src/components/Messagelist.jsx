export function Messagelist({messages, messageRef}) {
    return (
        <div className = "messageList">
            {messages.map((msg, index) => (
                <div 
                    key = {index}
                    className="messageBubble"
                >
                    {msg}
                </div>
            ))}
            <div ref = {messageRef} />
        </div>
    );
}