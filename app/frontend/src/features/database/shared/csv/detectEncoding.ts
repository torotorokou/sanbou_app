/**
 * エンコーディング検出ユーティリティ
 * 将来的な拡張用（現在は基本的にUTF-8を想定）
 */

export async function detectEncoding(_file: File): Promise<string> {
  // 基本実装: UTF-8を返す
  // 必要に応じてencoding-japanese等のライブラリを導入
  return 'utf-8';
}

export async function readFileAsText(file: File, encoding: string = 'utf-8'): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      resolve(text);
    };
    reader.onerror = () => {
      reject(new Error('ファイルの読み取りに失敗しました'));
    };
    reader.readAsText(file, encoding);
  });
}
