import React from 'react';
import { Result, Button } from 'antd';
import { useNavigate } from 'react-router-dom';

/**
 * 404 Not Found ページ
 * 
 * 存在しないルートにアクセスした際に表示されるエラーページ。
 * ユーザーをホームページに誘導します。
 * 
 * @component
 * @example
 * ```tsx
 * <Route path="*" element={<NotFoundPage />} />
 * ```
 */
export const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      minHeight: '100vh',
      padding: '24px'
    }}>
      <Result
        status="404"
        title="404"
        subTitle="お探しのページが見つかりません"
        extra={
          <Button type="primary" onClick={() => navigate('/')}>
            ホームに戻る
          </Button>
        }
      />
    </div>
  );
};

export default NotFoundPage;
