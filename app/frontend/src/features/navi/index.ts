/**
 * Navi Feature - Public API
 * MVVM+SOLID アーキテクチャに準拠した barrel export
 */

// Domain Types - DTO
export type {
    ChatQuestionRequestDto,
    ChatAnswerResponseDto,
    QuestionOptionsResponseDto,
} from './domain/types/dto';

// Domain Types - Domain Models
export type {
    MenuItem,
    CategoryTemplate,
    CategoryDataMap,
    ChatState,
    PdfPreviewState,
    ChatAnswer,
    StepItem,
} from './domain/types/types';

export {
    filterMenuItems,
    RagChatError,
} from './domain/types/types';

// Domain Services
export {
    normalizePdfUrl,
} from './domain/services/pdfUrlNormalizer';

// Ports
export type {
    NaviRepository,
} from './ports/repository';

// Model (ViewModel)
export { useNaviChat } from './model/useNaviVM';

// Infrastructure
export { NaviRepositoryImpl } from './infrastructure/navi.repository';

// UI Components (re-export with original names)
export { NaviLayout } from './ui/components/NaviLayout';
export { PdfReferenceButton } from './ui/components/PdfReferenceButton';
