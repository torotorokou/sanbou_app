/**
 * Shogun Catalog Hook
 * 将軍マニュアルのカタログ一覧を取得
 */
import React, { useEffect, useState } from 'react';
import {
  FileDoneOutlined,
  FolderOpenOutlined,
  FileProtectOutlined,
  FileTextOutlined,
  FileSearchOutlined,
  CloudUploadOutlined,
  DollarOutlined,
  FileSyncOutlined,
} from '@ant-design/icons';
import type { ManualSection } from '../model/types';
import { ShogunClient } from '../api/client';

// アイコンマッピング
const iconMap: Record<string, React.ReactNode> = {
  FileDoneOutlined: <FileDoneOutlined />,
  FolderOpenOutlined: <FolderOpenOutlined />,
  FileProtectOutlined: <FileProtectOutlined />,
  FileTextOutlined: <FileTextOutlined />,
  FileSearchOutlined: <FileSearchOutlined />,
  CloudUploadOutlined: <CloudUploadOutlined />,
  DollarOutlined: <DollarOutlined />,
  FileSyncOutlined: <FileSyncOutlined />,
};

export function useShogunCatalog() {
  const [sections, setSections] = useState<ManualSection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const ctrl = new AbortController();
    setLoading(true);
    
    ShogunClient.catalog(ctrl.signal)
      .then((data) => {
        const mapped = data.sections.map((sec: any) => ({
          id: sec.id,
          title: sec.title,
          icon: sec.icon ? iconMap[sec.icon] || <FileDoneOutlined /> : <FileDoneOutlined />,
          items: sec.items.map((item: any) => ({
            id: item.id,
            title: item.title,
            description: item.description,
            route: item.route,
            tags: item.tags || [],
            flowUrl: item.flow_url,
            videoUrl: item.video_url,
          })),
        }));
        setSections(mapped);
        setLoading(false);
      })
      .catch((err) => {
        if (err.name !== 'AbortError') {
          setError(err);
          setLoading(false);
        }
      });

    return () => ctrl.abort();
  }, []);

  return { sections, loading, error };
}
