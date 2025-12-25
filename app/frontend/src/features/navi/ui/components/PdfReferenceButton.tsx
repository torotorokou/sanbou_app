// features/navi/ui/PdfReferenceButton.tsx
// 参考PDFボタン（純粋なUI）

import React from "react";
import { Button } from "antd";
import { FilePdfOutlined } from "@ant-design/icons";

interface PdfReferenceButtonProps {
  pdfUrl: string | null;
  onClick: () => void;
}

export const PdfReferenceButton: React.FC<PdfReferenceButtonProps> = ({
  pdfUrl,
  onClick,
}) => {
  return (
    <div
      style={{
        width: "100%",
        maxWidth: "100%",
        position: "fixed",
        left: 0,
        bottom: 0,
        zIndex: 200,
        display: "flex",
        justifyContent: "center",
        pointerEvents: "none",
        paddingBottom: "max(8px, env(safe-area-inset-bottom))",
        boxSizing: "border-box",
      }}
    >
      <Button
        size="small"
        style={{
          width: 130,
          height: 32,
          borderRadius: 24,
          boxShadow: "0 4px 16px rgba(0,0,0,0.10)",
          background: "#fff",
          fontWeight: 600,
          transition: "all 0.3s ease",
          overflow: "hidden",
          whiteSpace: "nowrap",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 6,
          pointerEvents: "auto",
        }}
        disabled={!pdfUrl}
        onClick={onClick}
        onMouseEnter={(e) => {
          if (!pdfUrl) return;
          const btn = e.currentTarget;
          btn.style.width = "180px";
          btn.style.height = "48px";
          btn.style.fontSize = "16px";
          btn.style.padding = "0 24px";
        }}
        onMouseLeave={(e) => {
          const btn = e.currentTarget;
          btn.style.width = "130px";
          btn.style.height = "32px";
          btn.style.fontSize = "";
          btn.style.padding = "";
        }}
      >
        <FilePdfOutlined style={{ fontSize: 18 }} />
        参考PDF
      </Button>
    </div>
  );
};
