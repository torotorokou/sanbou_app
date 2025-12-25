import { describe, it, expect } from "vitest";
import { renderHook } from "@testing-library/react";
import { useFilterLayout } from "../useFilterLayout";
import * as sharedModule from "@/shared";

// useResponsiveをモック
vi.mock("@/shared", () => ({
  useResponsive: vi.fn(),
}));

describe("useFilterLayout", () => {
  it("デスクトップ（xl以上）レイアウトを返す", () => {
    vi.mocked(sharedModule.useResponsive).mockReturnValue({
      isDesktop: true,
      isMobile: false,
      isTablet: false,
    });

    const { result } = renderHook(() => useFilterLayout());

    expect(result.current.isDesktop).toBe(true);
    expect(result.current.categoryGrid).toEqual({ xs: 24, md: 24, xl: 5 });
    expect(result.current.modeGrid).toEqual({ xs: 24, md: 24, xl: 5 });
    expect(result.current.topNSortGrid).toEqual({ xs: 24, md: 24, xl: 14 });
  });

  it("モバイル（xl未満）レイアウトを返す", () => {
    vi.mocked(sharedModule.useResponsive).mockReturnValue({
      isDesktop: false,
      isMobile: true,
      isTablet: false,
    });

    const { result } = renderHook(() => useFilterLayout());

    expect(result.current.isDesktop).toBe(false);
    expect(result.current.modeGrid).toEqual({ xs: 24, md: 8, xl: 5 });
    expect(result.current.topNSortGrid).toEqual({ xs: 24, md: 16, xl: 14 });
  });

  it("期間・営業・フィルタグリッド設定が正しく返される", () => {
    vi.mocked(sharedModule.useResponsive).mockReturnValue({
      isDesktop: true,
      isMobile: false,
      isTablet: false,
    });

    const { result } = renderHook(() => useFilterLayout());

    expect(result.current.periodGrid).toEqual({ xs: 24, lg: 24 });
    expect(result.current.repSelectGrid).toEqual({ xs: 24, md: 18 });
    expect(result.current.filterGrid).toEqual({ xs: 24, md: 6 });
  });
});
