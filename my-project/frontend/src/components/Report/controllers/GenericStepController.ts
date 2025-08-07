// /app/src/components/Report/controllers/GenericStepController.ts
import type { ReportConfigPackage } from '../../../types/reportConfig';

export class GenericStepController {
    private currentStep: number = 0;
    private transitionHistory: Array<{
        from: number;
        to: number;
        timestamp: Date;
    }> = [];
    private config: ReportConfigPackage;
    private reportKey: string;

    constructor(config: ReportConfigPackage, reportKey: string) {
        this.config = config;
        this.reportKey = reportKey;
    }

    /**
     * 現在のステップを取得
     */
    getCurrentStep(): number {
        return this.currentStep;
    }

    /**
     * 指定したステップに遷移
     */
    executeTransition(
        targetStep: number,
        setCurrentStep: (step: number) => void,
        setIsLoading?: (loading: boolean) => void
    ): Promise<void> {
        return new Promise((resolve) => {
            const previousStep = this.currentStep;

            // 遷移履歴に記録
            this.transitionHistory.push({
                from: previousStep,
                to: targetStep,
                timestamp: new Date(),
            });

            // ローディング状態の設定
            if (setIsLoading) {
                setIsLoading(true);
            }

            // ステップを更新
            this.currentStep = targetStep;
            setCurrentStep(targetStep);

            console.log(
                `[${this.config.name}] Step transition: ${previousStep} → ${targetStep}`
            );

            // 非同期処理のシミュレーション
            setTimeout(() => {
                if (setIsLoading) {
                    setIsLoading(false);
                }
                resolve();
            }, 100);
        });
    }

    /**
     * バックエンド処理完了時のステップ遷移
     */
    onBackendComplete(
        setCurrentStep: (step: number) => void,
        setIsLoading?: (loading: boolean) => void
    ): Promise<void> {
        const reportType = this.config.getReportType(this.reportKey);

        if (reportType === 'auto') {
            // 自動処理の場合は完了ステップ（通常は最後のステップ）に移行
            const steps = this.config.getAllModalSteps(this.reportKey);
            const completionStep = steps.length - 1;
            return this.executeTransition(
                completionStep,
                setCurrentStep,
                setIsLoading
            );
        } else {
            // インタラクティブ処理の場合は次のステップに移行
            const nextStep = this.currentStep + 1;
            return this.executeTransition(
                nextStep,
                setCurrentStep,
                setIsLoading
            );
        }
    }

    /**
     * 前のステップに戻る
     */
    goToPreviousStep(
        setCurrentStep: (step: number) => void,
        setIsLoading?: (loading: boolean) => void
    ): Promise<void> {
        if (this.currentStep > 0) {
            return this.executeTransition(
                this.currentStep - 1,
                setCurrentStep,
                setIsLoading
            );
        }
        return Promise.resolve();
    }

    /**
     * 次のステップに進む
     */
    goToNextStep(
        setCurrentStep: (step: number) => void,
        setIsLoading?: (loading: boolean) => void
    ): Promise<void> {
        const steps = this.config.getAllModalSteps(this.reportKey);
        if (this.currentStep < steps.length - 1) {
            return this.executeTransition(
                this.currentStep + 1,
                setCurrentStep,
                setIsLoading
            );
        }
        return Promise.resolve();
    }

    /**
     * ステップをリセット
     */
    reset(
        setCurrentStep: (step: number) => void,
        setIsLoading?: (loading: boolean) => void
    ): void {
        this.currentStep = 0;
        this.transitionHistory = [];
        setCurrentStep(0);
        if (setIsLoading) {
            setIsLoading(false);
        }

        console.log(`[${this.config.name}] Step controller reset`);
    }

    /**
     * 遷移履歴を取得
     */
    getTransitionHistory(): Array<{
        from: number;
        to: number;
        timestamp: Date;
    }> {
        return [...this.transitionHistory];
    }

    /**
     * 現在のステップの設定を取得
     */
    getCurrentStepConfig() {
        const steps = this.config.getAllModalSteps(this.reportKey);
        return steps[this.currentStep] || null;
    }

    /**
     * 全ステップ数を取得
     */
    getTotalSteps(): number {
        return this.config.getAllModalSteps(this.reportKey).length;
    }

    /**
     * 指定したステップに進むことができるかチェック
     */
    canProceedToStep(targetStep: number): boolean {
        const steps = this.config.getAllModalSteps(this.reportKey);
        const stepConfig = steps[targetStep];

        if (!stepConfig) {
            return false;
        }

        // カスタム検証関数がある場合は実行
        if (stepConfig.canProceed) {
            return stepConfig.canProceed();
        }

        return true;
    }
}
