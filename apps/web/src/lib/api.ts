export interface User { id: string; name: string; email: string; role: 'student' | 'recruiter' }
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api${path}`, {
      ...options, credentials: 'same-origin', cache: 'no-store',
      headers: options.body instanceof FormData ? options.headers : { 'Content-Type': 'application/json', ...options.headers },
    });
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') throw error;
    throw new Error('Không kết nối được máy chủ. Kiểm tra backend cổng 8000.');
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body.detail;
    throw new Error(typeof detail === 'string' ? detail : Array.isArray(detail)
      ? detail.map((item: { msg: string }) => item.msg).join('; ')
      : `Yêu cầu thất bại (${response.status}). Kiểm tra backend và AI.`);
  }
  return response.status === 204 ? undefined as T : response.json();
}
export async function download(path: string, name: string) {
  const response = await fetch(`/api${path}`, { credentials: 'same-origin' });
  if (!response.ok) throw new Error('Không tải được CV hoặc bạn không có quyền truy cập.');
  const url = URL.createObjectURL(await response.blob());
  const link = document.createElement('a'); link.href = url; link.download = name;
  link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}
