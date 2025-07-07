export type ChatMessage = {
    role: 'user' | 'bot';
    content: string;
    sources?: {
        pdf: string;
        section_title: string;
        highlight: string;
    }[];
};
