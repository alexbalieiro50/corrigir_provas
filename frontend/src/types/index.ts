export type QuestionStatus = "correct" | "wrong" | "blank" | "invalid";

export interface AnswerItem {
  question: number;
  marked: string | null;
  correct: string | null;
  status: QuestionStatus;
  confidence: number;
}

export interface PageResult {
  page: number;
  totalQuestions: number;
  correct: number;
  wrong: number;
  blank: number;
  invalid: number;
  score: number;
  answers: AnswerItem[];
  processedImageBase64: string | null;
}

export interface CorrectionResponse extends PageResult {
  pages: PageResult[];
}

export interface ApiError {
  error: string;
  message: string;
}
