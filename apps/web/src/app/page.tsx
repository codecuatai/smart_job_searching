'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { ArrowDown, ArrowRight, ArrowUpRight, Check, ChevronDown, FileText, Menu, Sparkles, X } from 'lucide-react';
import { MOCK_CANDIDATES_PIPELINE, MOCK_JOBS } from '@/data/mockData';

type LandingRole = 'applicant' | 'recruiter';
const landingAvatarByCandidate: Record<string, string> = {
  'cand-001': '/avatars/nam-nguyen.svg',
  'cand-002': '/avatars/thu-thao.svg',
  'cand-003': '/avatars/hoang-nam.svg',
};
const landingCompanyAvatarByJob: Record<string, string> = {
  'job-01': '/company-avatars/vng.svg',
  'job-02': '/company-avatars/shopee.svg',
  'job-03': '/company-avatars/viettel.svg',
};

function Brand() {
  return <Link className="landing-brand" href="/" aria-label="UniTalent AI, trang chủ">
    <span className="landing-mark" aria-hidden="true"><i /><i /><i /></span>
    <span>UniTalent<span>AI</span></span>
  </Link>;
}

function ApplicantPreview() {
  return <div className="landing-product" data-ui="applicant-match-preview">
    <div className="product-window-top"><span className="product-window-mark">U</span><span>Không gian ứng viên · Minh họa</span><span className="product-live"><i /> Hồ sơ đã kết nối</span></div>
    <div className="product-content">
      <div className="product-title-row"><div><span className="product-overline">Việc làm gợi ý</span><h2>Cơ hội dành cho bạn</h2></div><span className="product-date">TP. Hồ Chí Minh</span></div>
      {MOCK_JOBS.slice(0, 3).map((job, index) => <div className={`product-job ${index === 0 ? 'product-job-featured' : ''}`} data-reveal key={job.id}>
        <span className="product-company-mark"><Image src={landingCompanyAvatarByJob[job.id] || '/company-avatars/default.svg'} alt={`Logo ${job.company}`} width={34} height={34} /></span>
        <span className="product-job-info"><strong>{job.title}</strong><small>{job.company} <span>·</span> {job.workType}</small></span>
        <span className="product-match"><strong>{job.matchScore}%</strong><small>phù hợp</small></span>
      </div>)}
      <div className="product-foot"><span><span className="product-foot-dot" /> 4 việc làm đang chờ bạn xem</span><span>CV của bạn · PDF</span></div>
    </div>
    <div className="product-note"><Sparkles size={15} /><span>Đồ án Microservices của bạn khớp với Java và Spring Boot</span></div>
  </div>;
}

function RecruiterPreview() {
  const candidates = MOCK_CANDIDATES_PIPELINE.slice(0, 3);
  return <div className="landing-product recruiter-product" data-ui="recruiter-shortlist-preview">
    <div className="product-window-top"><span className="product-window-mark">U</span><span>Không gian tuyển dụng · Minh họa</span><span className="product-live"><i /> Java Backend</span></div>
    <div className="product-content">
      <div className="product-title-row"><div><span className="product-overline">Hồ sơ ứng tuyển</span><h2>Ứng viên phù hợp</h2></div><span className="product-date">3 hồ sơ</span></div>
      {candidates.map((candidate, index) => <div className={`product-candidate ${index === 0 ? 'product-candidate-featured' : ''}`} data-reveal key={candidate.id}>
        <span className={`product-avatar product-avatar-${index}`}><Image src={candidate.avatarUrl || landingAvatarByCandidate[candidate.id] || '/avatars/default-student.svg'} alt={`Ảnh đại diện của ${candidate.name}`} width={35} height={35} /></span>
        <span className="product-job-info"><strong>{candidate.name}</strong><small>{candidate.targetRole}</small></span>
        <span className="product-match"><strong>{candidate.matchScore}%</strong><small>phù hợp</small></span>
      </div>)}
      <div className="product-review"><span><FileText size={16} /> CV & hồ sơ năng lực</span><span className="product-review-check"><Check size={13} /> Đã phân tích</span></div>
      <div className="product-foot"><span><span className="product-foot-dot" /> Mở hồ sơ để xem bằng chứng kỹ năng</span></div>
    </div>
  </div>;
}

function ApplicantEvidence() {
  return <div className="evidence-panel" data-ui="cv-evidence-preview">
    <div className="evidence-heading"><span className="evidence-file-icon"><FileText size={19} /></span><span><strong>NguyenVanNam_CV.pdf</strong><small>CV đã gửi · VNG Corporation</small></span><span className="evidence-status"><Check size={13} /> Đã nộp</span></div>
    <div className="evidence-match-line"><span>Độ phù hợp với vị trí</span><strong>94%</strong></div>
    <div className="evidence-track"><i style={{ width: '94%' }} /></div>
    <div className="evidence-skills"><span><Check size={13} /> Java 21</span><span><Check size={13} /> Spring Boot</span><span className="evidence-gap">Kubernetes cơ bản</span></div>
    <div className="evidence-footer"><span>Hồ sơ được gửi kèm theo từng đơn ứng tuyển</span><ArrowUpRight size={15} /></div>
  </div>;
}

function RecruiterEvidence() {
  return <div className="evidence-panel evidence-review-panel" data-ui="recruiter-cv-review-preview">
    <div className="evidence-heading"><span className="evidence-avatar"><Image src="/avatars/nam-nguyen.svg" alt="Ảnh đại diện của Nam Nguyễn" width={36} height={36} /></span><span><strong>Nam Nguyễn</strong><small>Junior Java Backend · ĐH Bách Khoa</small></span><span className="evidence-status"><Check size={13} /> Hồ sơ mẫu</span></div>
    <div className="evidence-score-row"><div><span>Độ phù hợp</span><strong>94%</strong></div><div><span>Dự án khai báo</span><strong>01</strong></div><div><span>Kỹ năng khai báo</span><strong>06</strong></div></div>
    <div className="evidence-project"><span>Dự án nổi bật</span><strong>E-Commerce Microservices & Realtime Analytics</strong><small>Java 21 · Spring Boot · Kafka · ClickHouse</small></div>
    <div className="evidence-footer"><span>CV đính kèm trong đơn ứng tuyển</span><ArrowUpRight size={15} /></div>
  </div>;
}

const faqs = [
  ['UniTalent AI dành cho ai?', 'Ứng viên muốn tìm công việc phù hợp với năng lực và nhà tuyển dụng muốn xem hồ sơ theo yêu cầu tuyển dụng.'],
  ['Tôi có thể dùng một CV cho nhiều công việc không?', 'Có. Tải CV lên hồ sơ một lần, chọn CV khi ứng tuyển. Mỗi đơn sẽ lưu lại đúng tệp đã gửi để nhà tuyển dụng xem.'],
  ['Hệ thống đánh giá phù hợp dựa trên điều gì?', 'Bản demo đối chiếu thông tin hồ sơ, kỹ năng và dự án với yêu cầu của từng vị trí. Tỷ lệ hiển thị giúp tham khảo, quyết định tuyển dụng vẫn do con người đưa ra.'],
  ['Tôi có cần tạo CV ngay trên hệ thống không?', 'Chưa cần. Bạn có thể dùng CV PDF sẵn có, dung lượng tối đa 5 MB. Tính năng tạo CV trực tiếp chưa nằm trong bản hiện tại.'],
];

export default function LandingPage() {
  const [role, setRole] = useState<LandingRole>('applicant');
  const [menuOpen, setMenuOpen] = useState(false);
  const [openFaq, setOpenFaq] = useState<number | null>(0);
  const [motionEnabled, setMotionEnabled] = useState(false);
  const applicant = role === 'applicant';

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    setMotionEnabled(true);
    let observer: IntersectionObserver | undefined;
    const frame = window.requestAnimationFrame(() => {
      observer = new IntersectionObserver(entries => entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer?.unobserve(entry.target);
        }
      }), { threshold: 0.08, rootMargin: '0px 0px -5% 0px' });
      document.querySelectorAll<HTMLElement>('[data-reveal]').forEach(item => observer?.observe(item));
    });
    return () => { window.cancelAnimationFrame(frame); observer?.disconnect(); };
  }, []);

  return <main className="landing-page" data-motion={motionEnabled ? 'enabled' : undefined}>
    <header className="landing-header">
      <div className="landing-header-inner"><Brand />
        <nav className={`landing-nav ${menuOpen ? 'landing-nav-open' : ''}`} aria-label="Điều hướng chính">
          <a href="#cach-hoat-dong" onClick={() => setMenuOpen(false)}>Cách hoạt động</a>
          <a href="#danh-cho-ai" onClick={() => setMenuOpen(false)}>Dành cho ai</a>
          <a href="#cau-hoi" onClick={() => setMenuOpen(false)}>Câu hỏi</a>
          <Link className="landing-mobile-login" href="/login">Đăng nhập <ArrowUpRight size={15} /></Link>
        </nav>
        <div className="landing-header-actions"><Link href="/login" className="landing-login">Đăng nhập</Link><Link href="/register" className="landing-header-cta">Bắt đầu <ArrowUpRight size={15} /></Link></div>
        <button type="button" className="landing-menu-button" aria-label={menuOpen ? 'Đóng menu' : 'Mở menu'} aria-expanded={menuOpen} onClick={() => setMenuOpen(!menuOpen)}>{menuOpen ? <X size={20} /> : <Menu size={20} />}</button>
      </div>
    </header>

    <section className="landing-hero">
      <div className="landing-hero-copy">
        <h1>Tìm việc bằng<br />năng lực thật.</h1>
        <p className="landing-hero-description">UniTalent AI giúp ứng viên tìm công việc hợp với hồ sơ, đồng thời giúp doanh nghiệp nhìn rõ năng lực phía sau mỗi CV.</p>
        <div className="landing-hero-actions"><Link href="/register" className="landing-primary">Tạo hồ sơ ứng viên <ArrowRight size={17} /></Link><a href="#cach-hoat-dong" className="landing-secondary">Xem cách hoạt động <ArrowDown size={15} /></a></div>
        <div className="landing-hero-aside"><span>Một hồ sơ. Nhiều cơ hội phù hợp.</span></div>
      </div>
      <div className="landing-hero-visual">
        <div className="landing-preview-switch" role="tablist" aria-label="Xem giao diện theo vai trò">
          <button type="button" role="tab" aria-selected={applicant} className={applicant ? 'selected' : ''} onClick={() => setRole('applicant')}>Ứng viên</button>
          <button type="button" role="tab" aria-selected={!applicant} className={!applicant ? 'selected' : ''} onClick={() => setRole('recruiter')}>Nhà tuyển dụng</button>
        </div>
        {applicant ? <ApplicantPreview /> : <RecruiterPreview />}
        <p className="landing-visual-caption"><span>Minh họa giao diện {applicant ? 'ứng viên' : 'tuyển dụng'}</span><span>Điểm thật tính sau đăng nhập <ChevronDown size={13} /></span></p>
      </div>
    </section>

    <section className="landing-proof" aria-label="Cách UniTalent AI kết nối" data-reveal>
      <p>Không chỉ đọc CV. <strong>Đặt năng lực vào đúng ngữ cảnh công việc.</strong></p>
      <span className="proof-symbol" aria-hidden="true">↗</span>
    </section>

    <section className="landing-section landing-flow" id="cach-hoat-dong" data-reveal>
      <div className="section-side"><p>Hồ sơ của bạn mở ra nhiều hướng đi, không chỉ một vị trí.</p></div>
      <div className="section-main">
        <h2>Một CV,<br />nhiều cơ hội.</h2>
        <p className="section-lead">Tải CV một lần, xem mức độ phù hợp với nhiều việc làm, rồi chọn đúng phiên bản để ứng tuyển.</p>
        <div className="flow-steps">
          <div className="flow-step" data-reveal><span className="flow-step-mark">A</span><div><strong>Tạo hồ sơ năng lực</strong><p>Thêm kỹ năng, dự án và CV PDF của bạn.</p></div><ArrowRight size={16} /></div>
          <div className="flow-step" data-reveal><span className="flow-step-mark">B</span><div><strong>Khám phá việc làm phù hợp</strong><p>Xem kỹ năng khớp, điểm còn thiếu và yêu cầu của từng công việc.</p></div><ArrowRight size={16} /></div>
          <div className="flow-step" data-reveal><span className="flow-step-mark">C</span><div><strong>Ứng tuyển kèm đúng CV</strong><p>Mỗi đơn lưu lại CV đã gửi để bạn và nhà tuyển dụng cùng theo dõi.</p></div><ArrowRight size={16} /></div>
        </div>
        <Link href="/student/jobs" className="landing-text-link">Khám phá việc làm <ArrowUpRight size={16} /></Link>
      </div>
      <div className="flow-art"><ApplicantEvidence /><div className="flow-art-note"><span>Hồ sơ → công việc</span><strong>Phù hợp được giải thích bằng kỹ năng và dự án.</strong></div></div>
    </section>

    <section className="landing-recruiter" id="danh-cho-ai" data-reveal>
      <div className="recruiter-copy"><h2>Đọc năng lực thật.</h2><p className="section-lead">Dành cho nhà tuyển dụng: đặt CV trong ngữ cảnh của vị trí tuyển dụng. Xem dự án, kỹ năng và điểm phù hợp trước khi mở cuộc trò chuyện.</p>
        <div className="recruiter-points"><p><Check size={15} /> Nhận CV đính kèm trong từng đơn</p><p><Check size={15} /> Xem kỹ năng liên quan và khoảng trống</p><p><Check size={15} /> Theo dõi ứng viên xuyên suốt quy trình</p></div>
        <Link href="/recruiter/candidates" className="landing-text-link">Xem không gian tuyển dụng <ArrowUpRight size={16} /></Link>
      </div>
      <div className="recruiter-showcase"><RecruiterEvidence /><p><span>Hồ sơ ứng viên</span><span>Dự án · Kỹ năng · CV</span></p></div>
    </section>

    <figure className="landing-photo-band" data-reveal><Image src="/landing/cv-review-editorial.png" alt="Ứng viên và nhà tuyển dụng cùng xem xét một hồ sơ CV" width={1536} height={1024} loading="lazy" /><figcaption>Để kỹ năng và dự án kể câu chuyện phía sau mỗi hồ sơ.</figcaption></figure>

    <section className="landing-roles" data-reveal>
      <div className="roles-heading"><h2>Đúng người,<br />đúng cơ hội.</h2></div>
      <div className="role-columns">
        <Link href="/student/jobs" className="role-column role-applicant" data-reveal><span className="role-number">A</span><h3>Ứng viên</h3><p>Nhìn ra công việc hợp với kỹ năng và dự án bạn đã làm.</p><span className="role-link">Tìm cơ hội phù hợp <ArrowUpRight size={16} /></span><div className="role-mini-ui" data-ui="applicant-role-summary"><span>Gợi ý minh họa</span><div className="mini-result"><strong>Java Backend</strong><b>94%</b></div><div className="mini-result"><strong>Data Analyst</strong><b>91%</b></div></div></Link>
        <Link href="/recruiter/candidates" className="role-column role-employer" data-reveal><span className="role-number">B</span><h3>Nhà tuyển dụng</h3><p>Đối chiếu hồ sơ ứng tuyển với kỹ năng vị trí đang cần.</p><span className="role-link">Tìm ứng viên <ArrowUpRight size={16} /></span><div className="role-mini-ui employer-mini-ui" data-ui="recruiter-role-summary"><span>Ứng viên minh họa</span><div className="mini-result"><strong>Nam Nguyễn</strong><b>94%</b></div><div className="mini-result"><strong>Ứng viên phù hợp</strong><b>92%</b></div></div></Link>
      </div>
    </section>

    <section className="landing-faq" id="cau-hoi" data-reveal>
      <div className="faq-title"><h2>Trước khi<br />bắt đầu.</h2><p>Những điều nên biết về hồ sơ, CV và gợi ý việc làm.</p></div>
      <div className="faq-list">{faqs.map(([question, answer], index) => <div className={`faq-item ${openFaq === index ? 'faq-item-open' : ''}`} data-reveal key={question}>
        <button type="button" aria-expanded={openFaq === index} onClick={() => setOpenFaq(openFaq === index ? null : index)}><span>{question}</span><span className="faq-toggle">{openFaq === index ? '−' : '+'}</span></button>
        {openFaq === index && <p>{answer}</p>}
      </div>)}</div>
    </section>

    <section className="landing-cta" data-reveal>
      <div className="cta-content"><h2>Hồ sơ tiếp theo<br />có thể là của bạn.</h2><p>Bắt đầu từ vị trí bạn đang tìm hoặc ứng viên bạn muốn gặp.</p><div><Link href="/register" className="cta-button">Bắt đầu với UniTalent AI <ArrowRight size={17} /></Link><Link href="/login" className="cta-login">Đã có tài khoản? Đăng nhập</Link></div></div>
      <div className="cta-paths" data-ui="landing-role-paths"><span>Chọn lối bắt đầu</span><Link href="/student/jobs"><strong>Ứng viên</strong><small>Tìm việc phù hợp</small><ArrowUpRight size={15} /></Link><Link href="/recruiter/candidates"><strong>Nhà tuyển dụng</strong><small>Xem hồ sơ ứng tuyển</small><ArrowUpRight size={15} /></Link></div>
    </section>

    <footer className="landing-footer"><Brand /><p>Định hướng bằng dữ liệu.<br />Phát triển bằng năng lực.</p><nav aria-label="Liên kết chân trang"><a href="#cach-hoat-dong">Cách hoạt động</a><a href="#danh-cho-ai">Vai trò</a><a href="#cau-hoi">Câu hỏi thường gặp</a><Link href="/login">Đăng nhập</Link></nav><span className="footer-copyright">© 2026 UniTalent AI</span></footer>
  </main>;
}
