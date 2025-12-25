/**
 * stripMarkdownForSnippet - 一覧用Markdownプレーンテキスト化
 *
 * 一覧表示用にMarkdown記号を除去してプレーンテキストに変換。
 * 詳細表示には使わない（詳細はMarkdownレンダリングする）。
 *
 * @param markdown - Markdown形式の文字列
 * @param maxLength - 最大文字数（デフォルト: 120）
 * @returns プレーンテキスト（Markdown記号なし）
 */
export function stripMarkdownForSnippet(
  markdown: string | null | undefined,
  maxLength: number = 120,
): string {
  // null/undefined対策
  if (!markdown) {
    return "";
  }

  let text = markdown;

  // 1. 見出し記号を除去 (^#{1,6}\s)
  text = text.replace(/^#{1,6}\s+/gm, "");

  // 2. 強調記号を除去 (**text**, __text__, *text*, _text_)
  text = text.replace(/(\*\*|__)(.*?)\1/g, "$2"); // **text** -> text
  text = text.replace(/(\*|_)(.*?)\1/g, "$2"); // *text* -> text

  // 3. 画像記法を除去 (![alt](url))
  text = text.replace(/!\[([^\]]*)\]\([^)]*\)/g, "$1");

  // 4. リンク記法をテキストのみに ([text](url) -> text)
  text = text.replace(/\[([^\]]+)\]\([^)]*\)/g, "$1");

  // 5. 箇条書き記号を除去 (-, *, 1., 2., etc)
  text = text.replace(/^[\s]*[-*+]\s+/gm, ""); // - item, * item
  text = text.replace(/^[\s]*\d+\.\s+/gm, ""); // 1. item

  // 6. コードブロック記号を除去 (```lang ... ```)
  text = text.replace(/```[a-z]*\n?/g, "");

  // 7. インラインコード記号を除去 (`code`)
  text = text.replace(/`([^`]+)`/g, "$1");

  // 8. 改行をスペースに変換
  text = text.replace(/\n/g, " ");

  // 9. 連続スペースを1つに正規化
  text = text.replace(/\s+/g, " ");

  // 10. 前後の空白を除去
  text = text.trim();

  // 11. 最大文字数で丸める
  if (text.length > maxLength) {
    text = text.substring(0, maxLength) + "…";
  }

  return text;
}
