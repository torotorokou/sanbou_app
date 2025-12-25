// src/components/chat/ChatSendButtonSection.tsx
import React from "react";
import { VerticalActionButton } from "@shared/ui";
import { SendOutlined } from "@ant-design/icons";

type Props = {
  onClick: () => void;
  disabled?: boolean;
};

const ChatSendButtonSection: React.FC<Props> = ({ onClick, disabled }) => (
  <div
    style={{
      width: 70,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      background: "transparent",
      minHeight: 0,
    }}
  >
    <VerticalActionButton
      icon={<SendOutlined />}
      text="質問を送信"
      onClick={onClick}
      disabled={disabled}
    />
  </div>
);

export default ChatSendButtonSection;
