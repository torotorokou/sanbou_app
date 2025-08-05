export interface ChatMessage {
    role: 'user' | 'bot';
    content: string;
    timestamp?: number;
    type?: string;
    sources?: Array<{
        title: string;
        url?: string;
        page?: number;
        pdf?: string;
        section_title?: string;
        highlight?: string;
    }>;
}
