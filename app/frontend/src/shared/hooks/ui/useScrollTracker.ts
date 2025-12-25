import { useEffect, useState } from "react";

export function useScrollTracker(
  ref: React.RefObject<HTMLElement>,
  deps: unknown[],
) {
  const [isAtBottom, setIsAtBottom] = useState(true);
  const [hasNewMessage, setHasNewMessage] = useState(false);

  const handleScroll = () => {
    const el = ref.current;
    if (!el) return;

    const isBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 50;
    setIsAtBottom(isBottom);
    if (isBottom) {
      setHasNewMessage(false);
    }
  };

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    el.addEventListener("scroll", handleScroll);
    return () => {
      el.removeEventListener("scroll", handleScroll);
    };
  }, [ref]);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    if (isAtBottom) {
      el.scrollTop = el.scrollHeight;
      setHasNewMessage(false);
    } else {
      setHasNewMessage(true);
    }
  }, deps);

  return { isAtBottom, hasNewMessage };
}
