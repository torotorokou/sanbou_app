import React from 'react';
import { Modal, Steps, Button } from 'antd';
import type { ReactNode } from 'react';

const { Step } = Steps;

export type ReportStepperModalProps = {
    open: boolean;
    steps: string[];
    currentStep: number;
    onNext: () => void;
    onClose?: () => void;
    children: ReactNode;
};

const ReportStepperModal: React.FC<ReportStepperModalProps> = ({
    open,
    steps,
    currentStep,
    onNext,
    onClose,
    children,
}) => {
    const isLast = currentStep === steps.length - 1;

    return (
        <Modal
            open={open}
            onCancel={onClose}
            footer={null}
            centered
            width={720}
            closable={false}
        >
            <Steps current={currentStep} style={{ marginBottom: 24 }}>
                {steps.map((title, idx) => (
                    <Step key={idx} title={title} />
                ))}
            </Steps>

            <div style={{ minHeight: 240 }}>{children}</div>

            <div style={{ textAlign: 'right', marginTop: 24 }}>
                <Button type="primary" onClick={onNext}>
                    {isLast ? '閉じる' : '次へ'}
                </Button>
            </div>
        </Modal>
    );
};

export default ReportStepperModal;
