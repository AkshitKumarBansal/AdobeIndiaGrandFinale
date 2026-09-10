import React from 'react';
import useTypingEffect from '../../hooks/useTypingEffect';
import { useTheme } from '../../contexts/ThemeContext';
import { getPdfChatStyles } from '../../styles/appStyles';

const AnimatedBotMessage = ({ message }) => {
    const { displayedText, isDone } = useTypingEffect(message.content);
    const { currentTheme } = useTheme();
    const styles = getPdfChatStyles(currentTheme);

    return (
        <div style={{...styles.chatMessage, ...styles.botMessage}}>
            {displayedText}
            {!isDone && <span style={{ animation: 'blink 1s step-end infinite' }}>|</span>}
        </div>
    );
};

export default AnimatedBotMessage;