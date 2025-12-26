// ChatQuestionSection.tsx
import React from "react";
import { useResponsive, isTabletOrHalf } from "@/shared";
import QuestionPanel from "../components/QuestionPanel";

type Props = {
  category: string;
  setCategory: (val: string) => void;
  tags: string[];
  setTag: (val: string[]) => void;
  template: string;
  setTemplate: (val: string) => void;
  question: string;
  setQuestion: (val: string) => void;
  // 関連PDFカードは削除済み
  // YAMLからのデータ
  categoryData?: Record<string, { title: string; tag: string[] }[]>;
};

// スタイルは親から渡すcardStyleを優先

const ChatQuestionSection: React.FC<Props> = ({
  category,
  setCategory,
  tags,
  setTag,
  template,
  setTemplate,
  question,
  setQuestion,
  categoryData,
}) => {
  const { width, isMobile } = useResponsive();
  const isNarrow = typeof width === "number" ? isTabletOrHalf(width) : false;

  return (
    <div
      style={{
        width: isNarrow ? "100%" : 420,
        maxWidth: "100%",
        padding: isMobile ? "8px 0" : 24,
        paddingBottom: isNarrow ? 8 : 88,
        overflow: isMobile ? "visible" : "auto",
        display: "flex",
        flexDirection: "column",
        gap: 12,
        minHeight: isMobile ? "auto" : 0,
      }}
    >
      {/* QuestionPanelをそのまま使う */}
      <QuestionPanel
        category={category}
        setCategory={setCategory}
        tags={tags}
        setTag={setTag}
        template={template}
        setTemplate={setTemplate}
        question={question}
        setQuestion={setQuestion}
        categoryData={categoryData}
      />
    </div>
  );
};

export default ChatQuestionSection;
