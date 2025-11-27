import { describe, it, expect } from 'vitest';
import { isMobile, isTabletOrHalf, isDesktop, ANT, tierOf } from '@/shared';

describe('breakpoints predicates', () => {
  it('mobile boundary', () => {
    expect(isMobile(ANT.md - 1)).toBe(true); // 767
    expect(isMobile(ANT.md)).toBe(false); // 768
  });

  it('tablet/half boundary', () => {
    expect(isTabletOrHalf(ANT.md)).toBe(true); // 768
    expect(isTabletOrHalf(ANT.xl - 1)).toBe(true); // 1199
    expect(isTabletOrHalf(ANT.xl)).toBe(false); // 1200
  });

  it('desktop boundary', () => {
    expect(isDesktop(ANT.xl - 1)).toBe(false); // 1199
    expect(isDesktop(ANT.xl)).toBe(true); // 1200
  });

  it('tierOf mapping', () => {
    expect(tierOf(ANT.md - 1)).toBe('mobile');
    expect(tierOf(ANT.md)).toBe('tabletHalf');
    expect(tierOf(ANT.xl - 1)).toBe('tabletHalf');
    expect(tierOf(ANT.xl)).toBe('desktop');
  });
});
