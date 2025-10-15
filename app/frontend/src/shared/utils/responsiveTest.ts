import { isMobile, isTabletOrHalf, isDesktop, ANT } from '@/shared/constants/breakpoints';
/**
 * レスポンシブデザインの動作確認用ユーティリティ
 *
 * 使用方法：
 * 1. ブラウザの開発者ツールを開く (F12)
 * 2. デバイスツールバーをクリック (Ctrl+Shift+M)
 * 3. 以下のデバイスサイズでテスト:
 */

export const RESPONSIVE_TEST_SIZES = {
    // スマートフォン
    iPhone12Pro: { width: 390, height: 844 },
    iPhoneSE: { width: 375, height: 667 },
    AndroidSmall: { width: 360, height: 640 },

    // タブレット
    iPad: { width: ANT.md, height: 1024 },
    iPadPro: { width: 1024, height: 1366 },
    AndroidTablet: { width: 800, height: 1280 },

    // デスクトップ
    SmallLaptop: { width: 1024, height: ANT.md },
    MediumDesktop: { width: 1366, height: ANT.md },
    FullHD: { width: 1920, height: 1080 },
    LargeScreen: { width: 2560, height: 1440 },
};

/**
 * テスト確認項目:
 * 📱 スマートフォン (320px - 767px):
 *   - サイドバーがDrawerに変更される
 *   - レイアウトが縦並びになる
 *   - フォントサイズが14pxになる
 *   - プレビューエリアの高さが350pxになる
 *
 * 📱 タブレット (768px - 1199px):
 *   - サイドバー幅が200pxになる
 *   - フォントサイズが15pxになる
 *   - プレビューエリアの高さが450pxになる
 *
 * 💻 小さなデスクトップ (1024px - 1365px):
 *   - 左パネル幅が320pxになる
 *   - 中央パネル幅が60pxになる
 *   - プレビューエリアの最小幅が500pxになる
 *
 * 💻 中型デスクトップ (1366px - 1599px):
 *   - 標準レイアウトが適用される
 *   - コンテンツのパディングが20pxになる
 *
 * 🖥️ 大型デスクトップ (1600px以上):
 *   - フォントサイズが17pxになる
 *   - コンテンツのパディングが24pxになる
 *   - カードの角丸が12pxになる
 */

// ブラウザのコンソールで使用するヘルパー関数
declare global {
    interface Window {
        testResponsive: (
            deviceName: keyof typeof RESPONSIVE_TEST_SIZES
        ) => void;
        showCurrentBreakpoint: () => void;
    }
}

if (typeof window !== 'undefined') {
    window.testResponsive = (deviceName) => {
        const size = RESPONSIVE_TEST_SIZES[deviceName];
        console.log(`📱 Testing ${deviceName}: ${size.width}x${size.height}`);
        console.log(
            '⚠️  Please use browser dev tools to set viewport size manually'
        );
    };

    window.showCurrentBreakpoint = () => {
        const width = window.innerWidth;
        let breakpoint = '';
        if (isMobile(width)) breakpoint = '📱 Mobile';
        else if (isTabletOrHalf(width)) breakpoint = '📱 Tablet';
        else if (isDesktop(width)) breakpoint = '🖥️ Desktop';
        console.log(`Current viewport: ${width}px - ${breakpoint}`);
    };
}
