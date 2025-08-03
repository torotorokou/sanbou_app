// src/utils/notify.ts
import { notification } from 'antd';

export const notifySuccess = (message: string, description?: string) => {
    notification.success({
        message,
        description,
        placement: 'topRight', // 右上に表示
        duration: 4, // 4秒で自動で消える
    });
};

export const notifyError = (message: string, description?: string) => {
    notification.error({
        message,
        description,
        placement: 'topRight',
        duration: 6,
    });
};

export const notifyInfo = (message: string, description?: string) => {
    notification.info({
        message,
        description,
        placement: 'topRight',
        duration: 5,
    });
};

export const notifyWarning = (message: string, description?: string) => {
    notification.warning({
        message,
        description,
        placement: 'topRight',
        duration: 5,
    });
};
