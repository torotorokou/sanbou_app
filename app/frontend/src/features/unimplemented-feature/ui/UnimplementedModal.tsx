import React from "react";
import { Modal, Typography } from "antd";
import { ExclamationCircleOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";

const { Title, Paragraph } = Typography;

interface UnimplementedModalProps {
  visible: boolean;
  onClose: () => void;
  featureName: string;
  description?: string;
}

/**
 * 未実装機能モーダルコンポーネント
 *
 * 🎯 目的：
 * - まだ実装されていない機能に対してユーザーに通知
 * - 統一されたUIで未実装状態を表示
 * - 了解ボタンでポータルページに自動遷移
 *
 * 📝 使用例：
 * ```tsx
 * <UnimplementedModal
 *   visible={isModalVisible}
 *   onClose={() => setIsModalVisible(false)}
 *   featureName="工場帳簿"
 *   description="この機能は現在開発中です。"
 * />
 * ```
 */
const UnimplementedModal: React.FC<UnimplementedModalProps> = ({
  visible,
  onClose,
  featureName,
  description = "この機能は現在開発中です。近日中にリリース予定ですので、今しばらくお待ちください。",
}) => {
  const navigate = useNavigate();

  const handleOk = () => {
    onClose();
    navigate("/");
  };

  return (
    <Modal
      open={visible}
      onCancel={undefined}
      closable={false}
      maskClosable={false}
      keyboard={false}
      centered
      width={500}
      footer={[
        <button
          key="ok"
          onClick={handleOk}
          style={{
            padding: "8px 24px",
            backgroundColor: "#1890ff",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor: "pointer",
            fontSize: "14px",
          }}
        >
          了解
        </button>,
      ]}
    >
      <div style={{ textAlign: "center", padding: "24px 0" }}>
        <ExclamationCircleOutlined
          style={{
            fontSize: "64px",
            color: "#faad14",
            marginBottom: "24px",
          }}
        />
        <Title level={3} style={{ marginBottom: "16px" }}>
          {featureName} - 未実装
        </Title>
        <Paragraph
          style={{
            fontSize: "16px",
            color: "#595959",
            lineHeight: "1.6",
          }}
        >
          {description}
        </Paragraph>
      </div>
    </Modal>
  );
};

export default UnimplementedModal;
