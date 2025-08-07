// /app/src/hooks/useReportConfig.ts
import { useMemo, createContext, useContext, createElement } from 'react';
import type React from 'react';
import type { ReportConfigPackage } from '../types/reportConfig';

/**
 * 帳票設定を管理するカスタムフック
 *
 * このフックにより、コンポーネントは特定の設定セットに直接依存せず、
 * プロパティとして渡された設定パッケージを使用できます。
 */
export const useReportConfig = (configPackage: ReportConfigPackage) => {
    const config = useMemo(() => {
        return {
            // 基本情報
            name: configPackage.name,
            reportKeys: configPackage.reportKeys,

            // ヘルパー関数
            getReportType: configPackage.getReportType,
            getReportKeysByType: configPackage.getReportKeysByType,
            getReportOptions: configPackage.getReportOptions,
            getAllModalSteps: configPackage.getAllModalSteps,

            // API設定
            getApiUrl: (reportKey: string) =>
                configPackage.apiUrlMap[reportKey],

            // CSV設定
            getCsvConfig: (reportKey: string) =>
                configPackage.csvConfigMap[reportKey],

            // PDF関連
            generatePdf: (reportKey: string) =>
                configPackage.pdfGeneratorMap[reportKey],
            getPreviewImage: (reportKey: string) =>
                configPackage.pdfPreviewMap[reportKey],

            // 元の設定オブジェクト（必要な場合）
            raw: configPackage,
        };
    }, [configPackage]);

    return config;
};

/**
 * 帳票設定パッケージ用のコンテキストプロバイダー
 *
 * アプリケーション全体で使用する設定パッケージを提供
 */
const ReportConfigContext = createContext<ReportConfigPackage | null>(null);

export const ReportConfigProvider: React.FC<{
    children: React.ReactNode;
    config: ReportConfigPackage;
}> = ({ children, config }) => {
    return (
        <ReportConfigContext.Provider value={config}>
            {children}
        </ReportConfigContext.Provider>
    );
};

/**
 * コンテキストから帳票設定を取得するフック
 */
export const useReportConfigContext = () => {
    const config = useContext(ReportConfigContext);
    if (!config) {
        throw new Error(
            'useReportConfigContext must be used within a ReportConfigProvider'
        );
    }
    return useReportConfig(config);
};
