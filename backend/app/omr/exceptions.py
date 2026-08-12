class OMRError(Exception):
    """Erro genérico e esperado do pipeline de OMR.

    Mensagens dessa exceção são seguras para mostrar ao usuário final
    (não contêm stack trace nem detalhes internos).
    """

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class InvalidFileError(OMRError):
    def __init__(self, message="Arquivo inválido ou formato não suportado."):
        super().__init__("invalid_file", message)


class UnreadableImageError(OMRError):
    def __init__(self, message="Não foi possível ler a imagem enviada."):
        super().__init__("unreadable_image", message)


class CardNotFoundError(OMRError):
    def __init__(self, message="Não foi possível localizar o cartão-resposta na imagem."):
        super().__init__("card_not_found", message)


class InvalidAnswerKeyError(OMRError):
    def __init__(self, message="Gabarito inválido ou vazio."):
        super().__init__("invalid_answer_key", message)


class QuestionCountMismatchError(OMRError):
    def __init__(self, message="Quantidade de questões do gabarito é incompatível com o template."):
        super().__init__("question_count_mismatch", message)


class ProcessingError(OMRError):
    def __init__(self, message="Erro ao processar o cartão-resposta."):
        super().__init__("processing_error", message)
