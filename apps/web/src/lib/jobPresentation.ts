export function jobSalary(raw: string) {
  if (!raw || /love it|attractive|negotiable|competitive/i.test(raw)) return 'Lương thỏa thuận';
  // Never invent currency when the crawler did not provide one.
  if (!/vnd|vnđ|usd|\$|triệu|million|\d\s*m\b/i.test(raw)) return `${raw} · chưa rõ đơn vị`;
  return raw;
}
export function jobLocation(raw: string) {
  return raw?.replace(/Not Available,?\s*/gi, '').trim() || 'Chưa có địa điểm';
}
export function jobDate(raw: string) {
  const date = new Date(raw);
  return Number.isNaN(date.getTime()) ? 'Chưa rõ ngày đăng' : date.toLocaleDateString('vi-VN');
}
