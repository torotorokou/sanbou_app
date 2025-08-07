/**
 * レポート生成ステップ制御ユーティリティ
 * モーダルのステップ進行を統一的に管理
 */

import type {
    ReportKey,
    ReportType,
} from '../../../constants/reportConfig/managementReportConfig';
import { getReportType } from '../../../constants/reportConfig/managementReportConfig';

export interface StepControlConfig {
    reportKey: ReportKey;
    reportType: ReportType;
    setCurrentStep: (step: number) => void;
    setLoading: (loading: boolean) => void;
    setFinalized: (finalized: boolean) => void;
}

export interface StepTransition {
    from: number;
    to: number;
    reason: string;
    reportType: ReportType;
}

/**
 * ステップ制御ロジック
 */
export class StepController {
    private config: StepControlConfig;
    private transitions: StepTransition[] = [];

    constructor(config: StepControlConfig) {
        this.config = config;
    }

    /**
     * ステップ遷移を記録付きで実行
     */
    private executeTransition(from: number, to: number, reason: string): void {
        const transition: StepTransition = {
            from,
            to,
            reason,
            reportType: this.config.reportType,
        };

        this.transitions.push(transition);

        console.log(
            `[StepController:${this.config.reportKey}] Step transition: ${from} → ${to} (${reason})`
        );

        this.config.setCurrentStep(to);
    }

    /**
     * レポート生成開始時の初期化
     */
    onReportStart(): void {
        console.log(
            `[StepController:${this.config.reportKey}] Report generation started`
        );
        this.executeTransition(-1, 0, 'Report generation start');
        this.config.setLoading(true);
    }

    /**
     * バックエンド処理完了時のステップ進行
     * autoタイプ: ZIP受信完了で次のステップへ
     * interactiveタイプ: ワークフロー制御に委譲
     */
    onBackendComplete(hasZipResult: boolean = false): void {
        const currentStep = this.getCurrentStep();

        if (this.config.reportType === 'auto') {
            if (hasZipResult && currentStep === 0) {
                // ZIP処理完了でステップ2（完了画面）へ
                this.executeTransition(
                    0,
                    1,
                    'Auto report ZIP processing completed'
                );
                this.config.setLoading(false);
                this.config.setFinalized(true);
            }
        } else {
            // インタラクティブレポートは個別に制御
            console.log(
                `[StepController:${this.config.reportKey}] Interactive report - step control delegated to workflow`
            );
        }
    }

    /**
     * 処理エラー時のステップリセット
     */
    onError(error: string): void {
        console.error(
            `[StepController:${this.config.reportKey}] Error occurred:`,
            error
        );
        this.config.setLoading(false);
        // ステップはそのままでローディングのみ停止
    }

    /**
     * 現在のステップを取得（仮想的 - 実際はReactステートから）
     */
    private getCurrentStep(): number {
        // 実際の実装では外部から現在のステップを取得
        // ここでは transitions の最後の to を使用
        if (this.transitions.length === 0) return 0;
        return this.transitions[this.transitions.length - 1].to;
    }

    /**
     * ステップ遷移履歴を取得（デバッグ用）
     */
    getTransitionHistory(): StepTransition[] {
        return [...this.transitions];
    }

    /**
     * ステップコントローラーをリセット
     */
    reset(): void {
        this.transitions = [];
        console.log(
            `[StepController:${this.config.reportKey}] Controller reset`
        );
    }
}

/**
 * StepControllerのファクトリー関数
 */
export const createStepController = (
    reportKey: ReportKey,
    setCurrentStep: (step: number) => void,
    setLoading: (loading: boolean) => void,
    setFinalized: (finalized: boolean) => void
): StepController => {
    const reportType = getReportType(reportKey);

    return new StepController({
        reportKey,
        reportType,
        setCurrentStep,
        setLoading,
        setFinalized,
    });
};
