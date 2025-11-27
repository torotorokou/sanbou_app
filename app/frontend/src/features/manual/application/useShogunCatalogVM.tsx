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
import type { ManualSection } from '../domain/types/shogun.types';
import { ShogunClient } from '../infrastructure/shogun.client';

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
        // Debug: Log raw catalog response to verify item.id presence
        console.log('[useShogunCatalog] Raw catalog response:', data);
        
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const mapped = data.sections.map((sec: any) => ({
          id: sec.id,
          title: sec.title,
          icon: sec.icon ? iconMap[sec.icon] || <FileDoneOutlined /> : <FileDoneOutlined />,
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
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
        
        // Debug: Log mapped items to verify id mapping
        console.log('[useShogunCatalog] Mapped sections with item ids:', 
          mapped.map(s => ({ 
            section: s.title, 
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            items: s.items.map((i: any) => ({ id: i.id, title: i.title })) 
          }))
        );
        
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
