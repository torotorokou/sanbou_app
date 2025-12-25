/**
 * notifyApiError のユニットテスト
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { notifyApiError } from "../../infrastructure/notify";
import { ApiError } from "@shared/types";
import * as notifyModule from "../../infrastructure/notify";

// モック
vi.mock("../model/notification.store", () => ({
  useNotificationStore: {
    getState: () => ({
      addNotification: vi.fn(() => "test-id"),
    }),
  },
}));

describe("notifyApiError", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("ApiError の code が INPUT_INVALID の場合、warning として通知", () => {
    const error = new ApiError("INPUT_INVALID", 422, "入力値が不正です");

    const notifySpy = vi.spyOn(notifyModule, "notifyWarning");

    notifyApiError(error);

    expect(notifySpy).toHaveBeenCalledWith(
      "入力エラー",
      "入力値が不正です",
      5000,
    );
  });

  it("ApiError の code が AUTH_REQUIRED の場合、error として通知", () => {
    const error = new ApiError("AUTH_REQUIRED", 401, "認証が必要です");

    const notifySpy = vi.spyOn(notifyModule, "notifyError");

    notifyApiError(error);

    expect(notifySpy).toHaveBeenCalledWith(
      "認証が必要です",
      "認証が必要です",
      6000,
    );
  });

  it("ApiError の code が INTERNAL_ERROR の場合、error として通知", () => {
    const error = new ApiError("INTERNAL_ERROR", 500, "処理に失敗しました");

    const notifySpy = vi.spyOn(notifyModule, "notifyError");

    notifyApiError(error);

    expect(notifySpy).toHaveBeenCalledWith(
      "処理に失敗しました",
      "処理に失敗しました",
      6000,
    );
  });

  it("ProblemDetails オブジェクトの場合、code に応じて通知", () => {
    const error = {
      code: "VALIDATION_ERROR",
      status: 422,
      userMessage: "バリデーションエラーが発生しました",
    };

    const notifySpy = vi.spyOn(notifyModule, "notifyWarning");

    notifyApiError(error);

    expect(notifySpy).toHaveBeenCalledWith(
      "入力値が不正です",
      "バリデーションエラーが発生しました",
      5000,
    );
  });

  it("不明なエラーの場合、デフォルトの error として通知", () => {
    const error = new Error("不明なエラー");

    const notifySpy = vi.spyOn(notifyModule, "notifyError");

    notifyApiError(error, "カスタムタイトル");

    expect(notifySpy).toHaveBeenCalledWith(
      "カスタムタイトル",
      "不明なエラー",
      6000,
    );
  });

  it("文字列エラーの場合、そのまま通知", () => {
    const notifySpy = vi.spyOn(notifyModule, "notifyError");

    notifyApiError("エラーメッセージ", "タイトル");

    expect(notifySpy).toHaveBeenCalledWith(
      "タイトル",
      "エラーメッセージ",
      6000,
    );
  });

  it("null/undefined の場合、デフォルトメッセージで通知", () => {
    const notifySpy = vi.spyOn(notifyModule, "notifyError");

    notifyApiError(null);

    expect(notifySpy).toHaveBeenCalledWith(
      "エラーが発生しました",
      "不明なエラーが発生しました",
      6000,
    );
  });
});
