import React, { useState, useEffect } from "react";
import { List, Tag, Typography } from "antd";
import { UnimplementedModal } from '@features/shared';

const { Title, Paragraph } = Typography;

interface Notice {
  id: number;
  title: string;
  content: string;
  isRead: boolean;
  isImportant?: boolean;
}

const initialNotices: Notice[] = [
  {
    id: 1,
    title: "新機能リリースのお知らせ",
    content: "9月20日に新しい帳票機能を追加しました。",
    isRead: false,
    isImportant: true,
  },
  {
    id: 2,
    title: "システムメンテナンス",
    content: "9月25日 2:00-5:00 にシステムメンテナンスを実施予定です。",
    isRead: false,
  },
  {
    id: 3,
    title: "定期バックアップ完了",
    content: "9月10日のバックアップが正常に完了しました。",
    isRead: true,
  },
];

const NoticeList: React.FC = () => {
  const [notices, setNotices] = useState<Notice[]>(initialNotices);
  const [showUnimplementedModal, setShowUnimplementedModal] = useState(false);

  useEffect(() => {
    // ページ読み込み時にモーダルを表示
    setShowUnimplementedModal(true);
  }, []);

  const markAsRead = (id: number) => {
    setNotices((prev) =>
      prev.map((n) => (n.id === id ? { ...n, isRead: true } : n))
    );
  };

  return (
    <div style={{ padding: 24 }}>
      <UnimplementedModal
        visible={showUnimplementedModal}
        onClose={() => setShowUnimplementedModal(false)}
        featureName="お知らせ"
        description="お知らせ機能は現在開発中です。完成まで今しばらくお待ちください。リリース後は、システムの更新情報や重要なお知らせをリアルタイムで受け取ることができます。"
      />
      <Title level={2}>お知らせ一覧</Title>

      <List
        itemLayout="vertical"
        dataSource={notices}
        renderItem={(item) => (
          <List.Item
            key={item.id}
            style={{
              background: item.isRead ? "#fff" : "#f0f8ff",
              borderLeft: item.isRead ? "none" : "4px solid #1890ff",
              cursor: "pointer",
              marginBottom: 12,
              borderRadius: 4,
              padding: 16,
            }}
            onClick={() => markAsRead(item.id)}
          >
            <List.Item.Meta
              title={
                <span style={{ fontWeight: item.isRead ? "normal" : "bold" }}>
                  {item.title}{" "}
                  {item.isImportant && (
                    <Tag color="red" style={{ marginLeft: 8 }}>
                      重要
                    </Tag>
                  )}
                </span>
              }
              description={<Paragraph>{item.content}</Paragraph>}
            />
          </List.Item>
        )}
      />
    </div>
  );
};

export default NoticeList;
