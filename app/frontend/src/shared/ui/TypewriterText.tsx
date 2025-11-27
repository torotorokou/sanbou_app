// TypewriterText.tsx
import React, { useEffect, useState } from 'react';

interface Props {
    text: string;
    speed?: number;
    onDone?: () => void; // ✅ 追加
}

const TypewriterText: React.FC<Props> = ({ text, speed = 30, onDone }) => {
    const [displayed, setDisplayed] = useState('');

    useEffect(() => {
        let i = 0;
        const timer = setInterval(() => {
            setDisplayed((prev) => prev + text[i]);
            i++;
            if (i === text.length) {
                clearInterval(timer);
                if (onDone) onDone(); // ✅ 終了時に通知
            }
        }, speed);
        return () => clearInterval(timer);
    }, [text, speed, onDone]);

    return <span>{displayed}</span>;
};

export default TypewriterText;
