import { useEffect, useState } from 'react';
import { BREAKPOINTS } from '../constants/breakpoints';

export type View = 'mobile' | 'tablet' | 'desktop';

export const useBreakpoint = (): View => {
  const getView = (): View => {
    if (typeof window === 'undefined') return 'desktop';
    const w = window.innerWidth;
    if (w <= BREAKPOINTS.mobile) return 'mobile';
    if (w <= BREAKPOINTS.tablet) return 'tablet';
    return 'desktop';
  };

  const [view, setView] = useState<View>(getView());

  useEffect(() => {
    const onResize = () => setView(getView());
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  return view;
};
