import { useState } from 'react'

export function Chatbar({messages, setMessages}) {
    const [isFocused, setIsFocused] = useState(false);
    const [currentText, setText] = useState("");

    const handleFocus = () => setIsFocused(true);
    const handleBlur = () => setIsFocused(false);
    const handleInputChange = (event) => {
        setText(event.target.value);
    };
    const handleKeyDown = (event) => {
        if (event.key === "Enter") {
            sendMessage();
        }
    };
    const sendMessage = () => {
        if (currentText.trim() !== "") {
            setMessages([...messages, { text: currentText, type: "sent"}]);
            setText("");
        }
    };

    return (
        <div className = "chatBar">
            <input 
                type = "text"
                value = {currentText}
                placeholder = {isFocused ? "" : "Type a message..."}
                onFocus = {handleFocus}
                onBlur = {handleBlur}
                onChange = {handleInputChange}
                onKeyDown = {handleKeyDown}
            />
            <button 
                className = "sendMessage"
                onClick = {sendMessage}
            />
        </div>
    );
}