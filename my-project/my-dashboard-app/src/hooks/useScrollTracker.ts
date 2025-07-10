import { useEffect, useState } from 'react';

export function useScrollTracker(
    ref: React.RefObject<HTMLElement>,
    deps: any[]
) {
    const [isAtBottom, setIsAtBottom] = useState(true);
    const [hasNewMessage, setHasNewMessage] = useState(false);

    const handleScroll = () => {
        const el = ref.current;
        if (!el) return;
        const isBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 50;
        setIsAtBottom(isBottom);
        if (isBottom) setHasNewMessage(false);
    };

    useEffect(() => {
        if (ref.current) {
            ref.current.addEventListener('scroll', handleScroll);
        }
        return () => {
            ref.current?.removeEventListener('scroll', handleScroll);
        };
    }, [ref]);

    useEffect(() => {
        if (isAtBottom && ref.current) {
            ref.current.scrollTop = ref.current.scrollHeight;
            setHasNewMessage(false);
        } else if (!isAtBottom) {
            setHasNewMessage(true);
        }
    }, deps);

    return { isAtBottom, hasNewMessage };
}
