import type { ApiError, CorrectionResponse } from "../types";

// Em desenvolvimento, o Vite faz proxy de /api para http://localhost:8000 (ver vite.config.ts)
const API_BASE = "/api";

export class ApiRequestError extends Error {
  code: string;
  constructor(err: ApiError) {
    super(err.message);
    this.code = err.error;
  }
}

export async function correctSheet(
  file: File,
  answerKeyText: string,
  templateName = "default_40"
): Promise<CorrectionResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("answer_key", answerKeyText);
  formData.append("template_name", templateName);

  let response: Response;
  try {
    response = await fetch(`${API_BASE}/correct`, {
      method: "POST",
      body: formData,
    });
  } catch (e) {
    throw new Error(
      "Não foi possível conectar ao servidor. Verifique se o backend está em execução (http://localhost:8000)."
    );
  }

  let data: unknown;
  try {
    data = await response.json();
  } catch {
    throw new Error("Resposta inválida do servidor.");
  }

  if (!response.ok) {
    const err = data as ApiError;
    throw new ApiRequestError(
      err && err.message ? err : { error: "unknown", message: "Erro desconhecido ao processar o cartão." }
    );
  }

  return data as CorrectionResponse;
}
