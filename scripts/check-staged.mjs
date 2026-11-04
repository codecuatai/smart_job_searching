import { execFileSync } from 'node:child_process';
const all = process.argv.includes('--all');
let names;
try {
  names = execFileSync('git', all ? ['ls-files', '-z'] : ['diff', '--cached', '--name-only', '--diff-filter=ACMR', '-z'], { encoding: 'utf8' }).split('\0').filter(Boolean);
} catch { console.error('Chạy tại thư mục repository sau git init.'); process.exit(1); }
const media = /\.(mp4|m4v|mov|avi|mkv|webm|wmv|flv|mpeg|mpg|mpe|m1v|m2v|3gp|3g2|mts|m2ts|mxf|vob|ogv|wav|mp3|m4a|aac|flac|ogg|opus|wma|aiff|aif|gif|heic|heif|psd|raw|cr2|nef|srt|vtt)$/i;
// TypeScript source (.ts) is source code; transport stream videos belong under media/.
const image = /\.(png|jpe?g|webp|bmp|tiff?)$/i;
const allowedImage = /^(apps\/web\/public\/|docs\/diagrams\/)/;
const violations = names.filter(name => /(^|\/)(media|uploads|recordings|videos|audio)\//i.test(name)
  || /(^|\/)(var|artifacts|node_modules|\.venv)\//i.test(name)
  || media.test(name)
  || (image.test(name) && !allowedImage.test(name))
  || (/(^|\/)\.env(?:\..*)?$/.test(name) && name !== '.env.example')
  || /\.(db|sqlite|sqlite3|pem|key)$/i.test(name)
  || /(^|\/)\.git\//.test(name));
for (const name of names) {
  try {
    const size = Number(execFileSync('git', ['cat-file', '-s', `:${name}`], { encoding: 'utf8' }).trim());
    if (size > 20 * 1024 * 1024 && !violations.includes(name)) violations.push(name);
  } catch { violations.push(name); }
}
if (violations.length) {
  console.error('Đã chặn media, dữ liệu riêng, bí mật hoặc file >20 MB trong Git:\n' + violations.join('\n'));
  console.error('Dùng git restore --staged -- <path> (hoặc git rm --cached -- <path> ở commit đầu). File cục bộ vẫn được giữ.');
  process.exit(1);
}
console.log(`Git check: ${names.length} file hợp lệ.`);
