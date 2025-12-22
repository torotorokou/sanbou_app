import { describe, it, expect } from 'vitest';
import { isMobile, isTabletOrHalf, isDesktop, ANT, tierOf } from '@/shared';
import { makeFlags } from '@/shared/hooks/ui/useResponsive';

describe('breakpoints predicates', () => {
  it('mobile boundary', () => {
    expect(isMobile(ANT.md - 1)).toBe(true); // 767
    expect(isMobile(ANT.md)).toBe(false); // 768
  });

  it('tablet/half boundary', () => {
    expect(isTabletOrHalf(ANT.md)).toBe(true); // 768
    expect(isTabletOrHalf(ANT.xl - 1)).toBe(true); // 1279
    expect(isTabletOrHalf(ANT.xl)).toBe(false); // 1280
  });

  it('desktop boundary', () => {
    expect(isDesktop(ANT.xl - 1)).toBe(false); // 1279
    expect(isDesktop(ANT.xl)).toBe(true); // 1280
  });

  it('tierOf mapping', () => {
    expect(tierOf(ANT.md - 1)).toBe('mobile');
    expect(tierOf(ANT.md)).toBe('tabletHalf');
    expect(tierOf(ANT.xl - 1)).toBe('tabletHalf');
    expect(tierOf(ANT.xl)).toBe('desktop');
  });
});

describe('useResponsive 3-tier flags', () => {
  it('767px should be Mobile', () => {
    const flags = makeFlags(767);
    expect(flags.isMobile).toBe(true);
    expect(flags.isTablet).toBe(false);
    expect(flags.isDesktop).toBe(false);
  });

  it('768px should be Tablet', () => {
    const flags = makeFlags(768);
    expect(flags.isMobile).toBe(false);
    expect(flags.isTablet).toBe(true);
    expect(flags.isDesktop).toBe(false);
  });

  it('1024px should still be Tablet (critical fix)', () => {
    const flags = makeFlags(1024);
    expect(flags.isMobile).toBe(false);
    expect(flags.isTablet).toBe(true);  // ★重要: 以前は false だった
    expect(flags.isLaptop).toBe(true);  // 詳細判定
    expect(flags.isDesktop).toBe(false);
  });

  it('1279px should be Tablet', () => {
    const flags = makeFlags(1279);
    expect(flags.isMobile).toBe(false);
    expect(flags.isTablet).toBe(true);
    expect(flags.isDesktop).toBe(false);
  });

  it('1280px should be Desktop', () => {
    const flags = makeFlags(1280);
    expect(flags.isMobile).toBe(false);
    expect(flags.isTablet).toBe(false);
    expect(flags.isDesktop).toBe(true);
  });

  it('isNarrow should be true for Mobile and Tablet', () => {
    expect(makeFlags(767).isNarrow).toBe(true);
    expect(makeFlags(768).isNarrow).toBe(true);
    expect(makeFlags(1279).isNarrow).toBe(true);
    expect(makeFlags(1280).isNarrow).toBe(false);
  });
});
