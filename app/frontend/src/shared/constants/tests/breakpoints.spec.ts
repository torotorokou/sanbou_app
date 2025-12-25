import { describe, it, expect } from "vitest";
import {
  isMobile,
  isTabletOrHalf,
  isDesktop,
  ANT,
  tierOf,
  makeFlags,
} from "@/shared";

describe("breakpoints predicates", () => {
  it("mobile boundary", () => {
    expect(isMobile(ANT.md - 1)).toBe(true); // 767
    expect(isMobile(ANT.md)).toBe(false); // 768
  });

  it("tablet/half boundary (2025-12-22更新)", () => {
    expect(isTabletOrHalf(ANT.md)).toBe(true); // 768
    expect(isTabletOrHalf(ANT.xl)).toBe(true); // 1280 ★変更: true（Tablet上限）
    expect(isTabletOrHalf(ANT.xl + 1)).toBe(false); // 1281
  });

  it("desktop boundary (2025-12-22更新)", () => {
    expect(isDesktop(ANT.xl)).toBe(false); // 1280 ★変更: false（Tablet扱い）
    expect(isDesktop(ANT.xl + 1)).toBe(true); // 1281 ★変更: true（Desktop開始）
  });

  it("tierOf mapping (2025-12-22更新)", () => {
    expect(tierOf(ANT.md - 1)).toBe("mobile");
    expect(tierOf(ANT.md)).toBe("tabletHalf");
    expect(tierOf(ANT.xl)).toBe("tabletHalf"); // 1280 ★変更: tabletHalf（Tablet扱い）
    expect(tierOf(ANT.xl + 1)).toBe("desktop"); // 1281 ★変更: desktop開始
  });
});

describe("useResponsive 3-tier flags", () => {
  it("767px should be Mobile", () => {
    const flags = makeFlags(767);
    expect(flags.isMobile).toBe(true);
    expect(flags.isTablet).toBe(false);
    expect(flags.isDesktop).toBe(false);
  });

  it("768px should be Tablet", () => {
    const flags = makeFlags(768);
    expect(flags.isMobile).toBe(false);
    expect(flags.isTablet).toBe(true);
    expect(flags.isDesktop).toBe(false);
  });

  it("1024px should still be Tablet (critical fix)", () => {
    const flags = makeFlags(1024);
    expect(flags.isMobile).toBe(false);
    expect(flags.isTablet).toBe(true); // ★重要: 以前は false だった
    expect(flags.isLaptop).toBe(true); // 詳細判定
    expect(flags.isDesktop).toBe(false);
  });

  it("1280px should be Tablet (2025-12-22変更)", () => {
    const flags = makeFlags(1280);
    expect(flags.isMobile).toBe(false);
    expect(flags.isTablet).toBe(true); // ★変更: true（Tablet上限）
    expect(flags.isDesktop).toBe(false); // ★変更: false
  });

  it("1281px should be Desktop (2025-12-22追加)", () => {
    const flags = makeFlags(1281);
    expect(flags.isMobile).toBe(false);
    expect(flags.isTablet).toBe(false);
    expect(flags.isDesktop).toBe(true); // ★Desktop開始
  });

  it("isNarrow should be true for Mobile and Tablet (2025-12-22更新)", () => {
    expect(makeFlags(767).isNarrow).toBe(true);
    expect(makeFlags(768).isNarrow).toBe(true);
    expect(makeFlags(1280).isNarrow).toBe(true); // ★変更: true（Tablet扱い）
    expect(makeFlags(1281).isNarrow).toBe(false); // ★変更: false（Desktop開始）
  });
});
