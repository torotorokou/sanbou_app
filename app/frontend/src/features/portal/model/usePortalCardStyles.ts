/**
 * PortalCardのスタイル計算ロジックを集約するカスタムフック
 */
import { useMemo } from "react";
import { theme } from "antd";
import { getGradient, getReadableTextColor } from "./colorUtils";
import {
  CARD_HEIGHT,
  BUTTON_WIDTH,
  BUTTON_HEIGHT,
  BUTTON_FONT_SIZE,
} from "../domain/constants";

interface PortalCardStyleConfig {
  color?: string;
  buttonWidth?: number;
  cardScale?: number;
  compactLayout?: boolean;
  hideButton?: boolean;
  smallButton?: boolean;
  heightScale?: number;
}

export const usePortalCardStyles = (config: PortalCardStyleConfig) => {
  const { token } = theme.useToken();
  const {
    color,
    buttonWidth,
    cardScale = 1,
    compactLayout = false,
    hideButton = false,
    smallButton = false,
    heightScale = 1,
  } = config;

  return useMemo(() => {
    const accent = color ?? token.colorPrimary;
    const accentPlate = getGradient(accent);
    const btnText = getReadableTextColor(accent);
    const appliedButtonWidth = buttonWidth ?? BUTTON_WIDTH;
    const scale = cardScale;

    // コンパクトレイアウト時の高さ
    const COMPACT_CARD_HEIGHT = 100;
    const appliedCardHeight = Math.round(
      (compactLayout ? COMPACT_CARD_HEIGHT : CARD_HEIGHT) * scale,
    );
    const appliedButtonHeight = Math.round(BUTTON_HEIGHT * scale);
    const appliedButtonFontSize = Math.round(BUTTON_FONT_SIZE * scale);
    const appliedButtonWidthScaled = Math.round(appliedButtonWidth * scale);
    const appliedIconSize = Math.round((compactLayout ? 40 : 56) * scale);
    const appliedIconFontSize = Math.round((compactLayout ? 20 : 28) * scale);

    // 小画面用のスケール
    const isSmallButton = !!smallButton;
    const SMALL_SCREEN_SCALE =
      hideButton && !isSmallButton ? 0.7 : isSmallButton ? 0.82 : 1;
    const hs = heightScale;

    // 最終的なサイズ計算
    const finalCardHeight = Math.round(
      appliedCardHeight * SMALL_SCREEN_SCALE * hs,
    );
    const finalIconSize = Math.round(appliedIconSize * SMALL_SCREEN_SCALE);
    const finalIconFontSize = Math.round(
      appliedIconFontSize * SMALL_SCREEN_SCALE,
    );
    const finalButtonHeight = Math.round(
      appliedButtonHeight * SMALL_SCREEN_SCALE,
    );
    const finalButtonWidth = Math.round(
      appliedButtonWidthScaled * SMALL_SCREEN_SCALE,
    );

    const isButtonHidden = !!hideButton && !isSmallButton;

    // タイトルフォントサイズの計算
    const titleFontSize = isSmallButton
      ? `clamp(14px, 3.6vw, 18px)`
      : hideButton
        ? "18px"
        : compactLayout
          ? `clamp(${Math.max(12, Math.round(appliedButtonFontSize * SMALL_SCREEN_SCALE))}px, 3.2vw, ${Math.round(appliedButtonFontSize * SMALL_SCREEN_SCALE) + 6}px)`
          : `clamp(${Math.max(12, Math.round((appliedButtonFontSize + 2) * SMALL_SCREEN_SCALE))}px, 2.4vw, ${Math.round((appliedButtonFontSize + 6) * SMALL_SCREEN_SCALE)}px)`;

    // 説明文フォントサイズの計算
    const descriptionFontSize = hideButton
      ? `clamp(12px, 2.6vw, 14px)`
      : `clamp(${Math.max(10, Math.round(12 * SMALL_SCREEN_SCALE))}px, 2.2vw, ${Math.round(14 * SMALL_SCREEN_SCALE)}px)`;

    // ボタンフォントサイズの計算
    const buttonFontSize = isSmallButton
      ? "12px"
      : `clamp(${Math.max(10, Math.round((appliedButtonFontSize - 2) * SMALL_SCREEN_SCALE))}px, 1.6vw, ${Math.round(appliedButtonFontSize * SMALL_SCREEN_SCALE)}px)`;

    return {
      accent,
      accentPlate,
      btnText,
      finalCardHeight,
      finalIconSize,
      finalIconFontSize,
      finalButtonHeight,
      finalButtonWidth,
      isButtonHidden,
      isSmallButton,
      titleFontSize,
      descriptionFontSize,
      buttonFontSize,
      scale,
      token,
    };
  }, [
    color,
    buttonWidth,
    cardScale,
    compactLayout,
    hideButton,
    smallButton,
    heightScale,
    token,
  ]);
};
