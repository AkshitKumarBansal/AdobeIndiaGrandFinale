import { useState, useEffect } from 'react';

// Custom hook for typing animation
const useTypingEffect = (textToType, speed = 20) => {
    const [displayedText, setDisplayedText] = useState('');
    const [isDone, setIsDone] = useState(false);

    useEffect(() => {
        setDisplayedText('');
        setIsDone(false);
        if (!textToType) return;

        let i = 0;
        const intervalId = setInterval(() => {
            if (i < textToType.length) {
                setDisplayedText(textToType.substring(0, i + 1));
                i++;
            } else {
                clearInterval(intervalId);
                setIsDone(true);
            }
        }, speed);

        return () => clearInterval(intervalId);
    }, [textToType, speed]);

    return { displayedText, isDone };
};

export default useTypingEffect;