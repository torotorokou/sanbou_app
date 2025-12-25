import React from "react";
import { Typography } from "antd";
import { AnswerViewer } from "../components/AnswerViewer";

type Props = {
  answer: string;
};

const ChatAnswerSection: React.FC<Props> = ({ answer }) => (
  <div
    style={{
      flex: 1,
      padding: 24,
      overflowY: "auto",
      minHeight: 0,
      width: "100%",
      maxWidth: "100%",
      boxSizing: "border-box",
      overflow: "hidden",
    }}
  >
    <Typography.Title level={4}>🤖 回答結果</Typography.Title>
    <AnswerViewer answer={answer} />
  </div>
);

export default ChatAnswerSection;
