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

// src/types/chat.ts
export type ChatAnswerResult = {
    answer: string;
    pdf_url?: string | null; // 返ってこない可能性もあるためオプショナル
};

export type ChatAnswerRequest = {
    query: string;
    category: string;
    tags: string[];
};
