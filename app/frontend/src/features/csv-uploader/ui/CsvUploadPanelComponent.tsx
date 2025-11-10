// TODO(kai): 呼び出し側を SimpleUploadPanel へ直接移行後、本アダプタを削除する
/**
 * Adapter: 旧 CsvUploadPanelComponent 互換レイヤ
 * - 旧呼び出し側の props を受けつつ、新 API（SimpleUploadPanel + useDatasetImportVM）へ委譲。
 * - 名前差/責務差はここで吸収（SOLID: DIP、Adapter パターン）。
 * 
 * 📋 参照元コミット: 76ab662 (my-project/frontend/src/components/database/CsvUploadPanel.tsx)
 * 
 * 🔄 互換性:
 * - 旧 CsvUploadPanel は upload.files と upload.makeUploadProps を受け取っていた
 * - 新 SimpleUploadPanel は items, onPickFile, onRemoveFile を受け取る
 * - このアダプタでその差分を吸収
 */
import React from "react";
import { SimpleUploadPanel } from "@/features/database/dataset-import/ui/SimpleUploadPanel";
import { useDatasetImportVM } from "@/features/database/dataset-import/hooks/useDatasetImportVM";
import type { CsvUploadPanelProps } from "../viewmodel/types";

export const CsvUploadPanelComponent: React.FC<CsvUploadPanelProps> = (props) => {
  const {
    datasetKey,
    // accept, maxSizeMB, onSuccess, onError は現時点では未使用
    // 将来的に必要に応じて実装
    ...rest
  } = props;

  // 新 API を使用
  const vm = useDatasetImportVM({
    datasetKey,
    // activeTypes は呼び出し側から渡されるべきだが、
    // 互換性のため、datasetKey から推測するか、空配列にする
    activeTypes: rest.activeTypes as string[] | undefined,
  });

  // 成功/エラーハンドリングは親コンポーネントに委譲
  // 必要に応じて vm.doUpload の結果をラップして onSuccess/onError を呼ぶ

  return (
    <SimpleUploadPanel
      items={vm.panelFiles}
      onPickFile={vm.onPickFile}
      onRemoveFile={vm.onRemoveFile}
      size="normal"
      showTitle={true}
    />
  );
};

export default CsvUploadPanelComponent;
