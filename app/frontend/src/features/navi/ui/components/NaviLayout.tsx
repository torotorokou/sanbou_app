// features/navi/ui/NaviLayout.tsx
// Naviページのレイアウトコンポーネント（状態を持たない純粋UI）

import React from "react";
import { Spin } from "antd";
import { ReportStepIndicator } from "@shared/ui";
import {
  ChatQuestionSection,
  ChatSendButtonSection,
  ChatAnswerSection,
  PdfPreviewModal,
} from "@features/chat";
import { useResponsive, bp, isTabletOrHalf } from "@/shared";
import type { CategoryDataMap, StepItem } from "../../domain/types/types";

interface NaviLayoutProps {
  // 状態
  loading: boolean;
  currentStep: number;
  category: string;
  tags: string[];
  template: string;
  question: string;
  answer: string;
  categoryData: CategoryDataMap;
  pdfModalVisible: boolean;
  pdfToShow: string | null;

  // セッター
  setCategory: (val: string) => void;
  setTags: (val: string[] | ((prev: string[]) => string[])) => void;
  setTemplate: (val: string) => void;
  setQuestion: (val: string) => void;
  setCurrentStep: (step: number) => void;
  setPdfModalVisible: (visible: boolean) => void;
  setPdfToShow: (url: string | null) => void;

  // アクション
  handleSearch: () => Promise<void>;

  // その他
  stepItems: StepItem[];
}

export const NaviLayout: React.FC<NaviLayoutProps> = ({
  loading,
  currentStep,
  category,
  tags,
  template,
  question,
  answer,
  categoryData,
  pdfModalVisible,
  pdfToShow,
  setCategory,
  setTags,
  setTemplate,
  setQuestion,
  setCurrentStep,
  setPdfModalVisible,
  setPdfToShow,
  handleSearch,
  stepItems,
}) => {
  const { width, isMobile } = useResponsive();
  const isNarrow = typeof width === "number" ? isTabletOrHalf(width) : false;
  const isMd =
    typeof width === "number" ? width >= bp.md && width < bp.xl : false;

  return (
    <div
      className="navi-page"
      style={{
        height: "100%",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        position: "relative",
      }}
    >
      {loading && <Spin tip="AIが回答中です..." size="large" fullscreen />}

      <div style={{ padding: isMobile ? "4px 8px" : "12px 24px" }}>
        <ReportStepIndicator currentStep={currentStep} items={stepItems} />
      </div>

      <div
        style={{
          display: "flex",
          flexDirection: isMobile ? "column" : "row",
          flex: 1,
          overflow: isMobile ? "auto" : "hidden",
          overflowX: "hidden",
          minHeight: 0,
          height: "100%",
          gap: isMobile ? 16 : 0,
          maxWidth: "100%",
        }}
      >
        {isMobile ? (
          /* モバイル: 縦積みレイアウト */
          <>
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                padding: "0 8px",
                maxWidth: "100%",
                width: "100%",
              }}
            >
              <ChatQuestionSection
                category={category}
                setCategory={(val) => {
                  setCategory(val);
                  setCurrentStep(1);
                  setTags([]);
                  setTemplate("自由入力");
                }}
                tags={tags}
                setTag={setTags}
                template={template}
                setTemplate={(val) => {
                  setTemplate(val);
                  if (val !== "自由入力") {
                    setQuestion(val);
                    setCurrentStep(2);
                  }
                }}
                question={question}
                setQuestion={(val) => {
                  setQuestion(val);
                  if (val.trim()) setCurrentStep(2);
                }}
                categoryData={categoryData}
              />

              <div
                style={{
                  padding: "16px 0",
                  display: "flex",
                  justifyContent: "center",
                }}
              >
                <ChatSendButtonSection
                  onClick={handleSearch}
                  disabled={!question.trim() || tags.length === 0 || loading}
                />
              </div>

              {/* 回答がある場合、下にスクロールを促すインジケーター */}
              {answer && (
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    padding: "8px 0",
                    color: "#1890ff",
                    fontSize: 13,
                    animation: "bounce 1.5s infinite",
                  }}
                >
                  <span>↓ 回答が生成されました ↓</span>
                  <span style={{ fontSize: 20, marginTop: 4 }}>▼</span>
                </div>
              )}
            </div>

            {/* 回答エリア */}
            <div
              style={{
                minHeight: 400,
                padding: "0 8px 16px",
                maxWidth: "100%",
                width: "100%",
              }}
            >
              <ChatAnswerSection answer={answer} />
            </div>
          </>
        ) : isNarrow ? (
          <>
            <div
              style={{
                display: "flex",
                flex: isMd ? "1 1 50%" : "1 1 40%",
                flexDirection: "column",
                minHeight: 0,
                overflow: "hidden",
              }}
            >
              <ChatQuestionSection
                category={category}
                setCategory={(val) => {
                  setCategory(val);
                  setCurrentStep(1);
                  setTags([]);
                  setTemplate("自由入力");
                }}
                tags={tags}
                setTag={setTags}
                template={template}
                setTemplate={(val) => {
                  setTemplate(val);
                  if (val !== "自由入力") {
                    setQuestion(val);
                    setCurrentStep(2);
                  }
                }}
                question={question}
                setQuestion={(val) => {
                  setQuestion(val);
                  if (val.trim()) setCurrentStep(2);
                }}
                categoryData={categoryData}
              />

              <div
                style={{
                  padding: "8px 8px",
                  display: "flex",
                  justifyContent: "center",
                  marginTop: 8,
                }}
              >
                <ChatSendButtonSection
                  onClick={handleSearch}
                  disabled={!question.trim() || tags.length === 0 || loading}
                />
              </div>
            </div>

            {/* 右カラム（回答） */}
            <div
              style={{
                flex: isMd ? "1 1 50%" : "1 1 60%",
                minHeight: 0,
                height: "100%",
                overflow: "hidden",
                width: 0,
                minWidth: 0,
              }}
            >
              <div
                className="navi-scroll-area"
                style={{
                  height: "100%",
                  minHeight: 0,
                  overflowY: "auto",
                  WebkitOverflowScrolling: "touch" as unknown as undefined,
                  width: "100%",
                  maxWidth: "100%",
                }}
              >
                <ChatAnswerSection answer={answer} />
              </div>
            </div>
          </>
        ) : (
          /* 通常の 3 列レイアウト */
          <>
            {/* 左カラム */}
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                minHeight: 0,
                overflow: "hidden",
                flex: "0 1 auto",
              }}
            >
              <ChatQuestionSection
                category={category}
                setCategory={(val) => {
                  setCategory(val);
                  setCurrentStep(1);
                  setTags([]);
                  setTemplate("自由入力");
                }}
                tags={tags}
                setTag={setTags}
                template={template}
                setTemplate={(val) => {
                  setTemplate(val);
                  if (val !== "自由入力") {
                    setQuestion(val);
                    setCurrentStep(2);
                  }
                }}
                question={question}
                setQuestion={(val) => {
                  setQuestion(val);
                  if (val.trim()) setCurrentStep(2);
                }}
                categoryData={categoryData}
              />
            </div>

            {/* 中央カラム */}
            <ChatSendButtonSection
              onClick={handleSearch}
              disabled={!question.trim() || tags.length === 0 || loading}
            />

            {/* 右カラム */}
            <div
              style={{
                minHeight: 0,
                height: "100%",
                flex: "1 1 auto",
                overflow: "hidden",
                width: 0,
                minWidth: 0,
              }}
            >
              <div
                className="navi-scroll-area"
                style={{
                  height: "100%",
                  minHeight: 0,
                  overflowY: "auto",
                  WebkitOverflowScrolling: "touch" as unknown as undefined,
                  width: "100%",
                  maxWidth: "100%",
                }}
              >
                <ChatAnswerSection answer={answer} />
              </div>
            </div>
          </>
        )}
      </div>

      {/* モーダルPDFプレビュー */}
      {pdfToShow && (
        <PdfPreviewModal
          visible={pdfModalVisible}
          pdfUrl={pdfToShow}
          onClose={() => {
            setPdfToShow(null);
            setPdfModalVisible(false);
          }}
        />
      )}
    </div>
  );
};
