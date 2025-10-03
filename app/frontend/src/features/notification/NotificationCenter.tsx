import React from 'react';
import { useNotificationStore } from './store';

export const NotificationCenter: React.FC = () => {
  const { notifications, removeNotification } = useNotificationStore();
  return (
    <div style={{
      position: 'fixed', top: 16, right: 16, zIndex: 9999,
      display: 'flex', flexDirection: 'column', gap: 8, width: 360,
    }}>
      {notifications.map(n => (
        <div key={n.id} style={{
          background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8,
          boxShadow: '0 8px 20px rgba(0,0,0,.08)', padding: 12,
        }}>
          <div style={{ fontWeight: 600, marginBottom: 4 }}>
            {n.title} <small style={{ color:'#999' }}>({n.type})</small>
          </div>
          {n.message && <div style={{ color:'#444', marginBottom: 8 }}>{n.message}</div>}
          <div style={{ textAlign: 'right' }}>
            <button onClick={() => removeNotification(n.id)} style={{
              border: '1px solid #ddd', background:'#fafafa', borderRadius:6, padding:'4px 10px', cursor:'pointer'
            }}>閉じる</button>
          </div>
        </div>
      ))}
    </div>
  );
};

export default NotificationCenter;
