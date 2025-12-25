/**
 * DragDropCsv - CSVファイル選択コンポーネント（ドラッグ&ドロップ + クリック対応）
 *
 * hidden input + ref でファイル選択ダイアログを開く
 * カード全体がクリック可能エリアとなり、キーボード操作にも対応
 * ドラッグ&ドロップでもCSVファイルをアップロード可能
 */

import React, { useRef, useState } from "react";
import { UploadOutlined } from "@ant-design/icons";

export interface DragDropCsvProps {
  typeKey: string;
  disabled?: boolean;
  onPickFile: (typeKey: string, file: File) => void;
  /** コンパクト表示 */
  compact?: boolean;
}

export const DragDropCsv: React.FC<DragDropCsvProps> = ({
  typeKey,
  disabled,
  onPickFile,
  compact = false,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleClick = () => {
    if (!disabled) {
      fileInputRef.current?.click();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!disabled && (e.key === "Enter" || e.key === " ")) {
      e.preventDefault();
      fileInputRef.current?.click();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onPickFile(typeKey, file);
      // input をリセットして同じファイルを再選択可能に
      e.target.value = "";
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled && !isDragging) {
      setIsDragging(true);
    }
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    // relatedTarget が null または div の外側の場合のみ状態をリセット
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX;
    const y = e.clientY;

    // マウスが完全に要素の外に出た場合のみリセット
    if (x < rect.left || x >= rect.right || y < rect.top || y >= rect.bottom) {
      setIsDragging(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (disabled) return;

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      const file = files[0];
      // CSVファイルかどうかチェック
      if (
        file.name.toLowerCase().endsWith(".csv") ||
        file.type === "text/csv"
      ) {
        onPickFile(typeKey, file);
      }
    }
  };

  return (
    <div
      role="button"
      tabIndex={disabled ? -1 : 0}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: compact ? "12px 8px" : "16px 12px",
        cursor: disabled ? "not-allowed" : "pointer",
        borderRadius: 4,
        transition: "background-color 0.2s, border-color 0.2s",
        backgroundColor: disabled
          ? "#fafafa"
          : isDragging
            ? "#e6f7ff"
            : "#ffffff",
        border: isDragging ? "2px dashed #1890ff" : "1px dashed #d9d9d9",
        opacity: disabled ? 0.5 : 1,
        pointerEvents: disabled ? "none" : "auto",
      }}
      onMouseEnter={(e) => {
        if (!disabled && !isDragging) {
          e.currentTarget.style.backgroundColor = "#f5f5f5";
          e.currentTarget.style.borderColor = "#1890ff";
        }
      }}
      onMouseLeave={(e) => {
        if (!disabled && !isDragging) {
          e.currentTarget.style.backgroundColor = "#ffffff";
          e.currentTarget.style.borderColor = "#d9d9d9";
        }
      }}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept=".csv"
        onChange={handleFileChange}
        style={{ display: "none" }}
        disabled={disabled}
      />
      <UploadOutlined
        style={{
          fontSize: compact ? 20 : 24,
          color: disabled ? "#bfbfbf" : "#1890ff",
          marginBottom: 4,
        }}
      />
      <div
        style={{
          fontSize: compact ? 12 : 13,
          color: disabled ? "#bfbfbf" : "#666",
          textAlign: "center",
        }}
      >
        {isDragging
          ? "ここにドロップ"
          : "クリック または ドラッグ&ドロップで CSV をアップロード"}
      </div>
    </div>
  );
};
