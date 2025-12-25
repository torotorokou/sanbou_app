/**
 * ポータルメニューの定義
 */
import React from "react";
import {
  BookOutlined,
  DashboardOutlined,
  RobotOutlined,
  FileTextOutlined,
  CloudUploadOutlined,
  SettingOutlined,
  NotificationOutlined,
  BarChartOutlined,
} from "@ant-design/icons";
import { ROUTER_PATHS } from "@app/routes/routes";
import type { PortalCardProps } from "../model/types";
import { PALETTE } from "../domain/constants";

export const portalMenus: PortalCardProps[] = [
  {
    title: "ダッシュボード",
    description: "複数のダッシュボードをまとめて表示します。",
    detail:
      "工場別・顧客別・価格表などの管理ダッシュボードへアクセスできます。表示中のダッシュボードを切り替えて詳細を確認してください。",
    icon: <DashboardOutlined />,
    link: ROUTER_PATHS.DASHBOARD_UKEIRE,
    color: PALETTE.OCEAN,
  },
  {
    title: "アナリティクス",
    description: "売上・顧客データの多角的な分析を行います。",
    detail:
      "営業・売上ツリーや顧客リスト分析など、データに基づく洞察を得られます。経営判断や営業戦略の立案をサポートします。",
    icon: <BarChartOutlined />,
    link: ROUTER_PATHS.SALES_TREE,
    color: PALETTE.LAVENDER,
  },
  {
    title: "帳簿作成",
    description: "各種帳簿の作成を行います。",
    detail:
      "工場日報や管理表などの帳簿作成とエクセル・PDFのエクスポートが可能です。テンプレートで入力を簡素化できます。",
    icon: <BookOutlined />,
    link: ROUTER_PATHS.REPORT_MANAGE,
    color: PALETTE.MINT,
  },
  {
    title: "参謀 NAVI",
    description: "AI アシスタントで業務を効率化します。",
    detail:
      "自然言語で質問 → マニュアル検索、帳簿補助、データ要約、定型処理の自動提案。内部データのみを安全に活用します。",
    icon: <RobotOutlined />,
    link: ROUTER_PATHS.NAVI,
    color: PALETTE.CORAL,
  },
  {
    title: "マニュアル",
    description: "社内手順書・運用ガイドを参照できます。",
    detail:
      "部署別の手順書、FAQ、オンボーディング資料を検索。更新履歴や担当者情報も確認できます。",
    icon: <FileTextOutlined />,
    link: ROUTER_PATHS.MANUALS,
    color: PALETTE.GOLD,
  },
  {
    title: "データベース",
    description: "データセットのインポートや保存データの閲覧・管理。",
    detail:
      "データセットインポート、レコード検索・編集・エクスポート、インポート履歴のトラッキングを行えます。",
    icon: <CloudUploadOutlined />,
    link: ROUTER_PATHS.DATASET_IMPORT,
    color: PALETTE.PURPLE,
  },
  {
    title: "管理機能",
    description: "システム設定や権限管理を行います。",
    detail:
      "ユーザー権限、システム構成、外部連携の設定。操作履歴やログの確認も可能です（管理者向け）。",
    icon: <SettingOutlined />,
    link: ROUTER_PATHS.SETTINGS,
    color: PALETTE.CYAN,
  },
  {
    title: "お知らせ",
    description: "最新のお知らせ・更新情報を確認。",
    detail:
      "メンテナンス情報、リリースノート、社内イベント、法令改正などを掲載します。",
    icon: <NotificationOutlined />,
    link: ROUTER_PATHS.NEWS,
    color: PALETTE.GRAY,
  },
];
