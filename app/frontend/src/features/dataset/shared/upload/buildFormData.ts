/**
 * FormData構築ユーティリティ
 */

export function buildFormData(filesByType: Record<string, File>): FormData {
  const form = new FormData();
  Object.entries(filesByType).forEach(([typeKey, file]) => {
    form.append(typeKey, file);
  });
  return form;
}
