import pytest
from services.api.app.data_quality import canonical_skills, parse_salary, classify_origin


@pytest.mark.parametrize('text,lo,hi,currency,period', [
    ('15.000.000 - 20.000.000 VNĐ', 15000000, 20000000, 'VND', 'MONTH'),
    ('15,5 - 20 triệu/tháng', 15500000, 20000000, 'VND', 'MONTH'),
    ('$1,500 - $2,000/month', 1500, 2000, 'USD', 'MONTH'),
    ('60k - 80k USD/year', 60000, 80000, 'USD', 'YEAR'),
    ('Từ 20 triệu', 20000000, None, 'VND', 'MONTH'),
    ('Up to 2000 USD', None, 2000, 'USD', 'MONTH'),
    ('15M – 22M VNĐ',15000000,22000000,'VND','MONTH'),
    ('14 – 16 million VND/month',14000000,16000000,'VND','MONTH'),
    ('12-15 Mil VND',12000000,15000000,'VND','MONTH'),
    ('Up to 30m++ VND',None,30000000,'VND','MONTH'),
])
def test_salary_units(text, lo, hi, currency, period):
    result = parse_salary(text)
    assert (result['minimum'], result['maximum'], result['currency'], result['period']) == (lo, hi, currency, period)


def test_ambiguous_salary_and_aliases():
    assert parse_salary('10-20')['status'] == 'unknown'
    assert parse_salary('10-20 VND')['status'] == 'unknown'
    assert parse_salary('Thỏa thuận')['status'] == 'negotiable'
    assert canonical_skills(['ReactJS', 'react', 'k8s']) == ['Kubernetes', 'React']
    assert classify_origin({}, email='student-123@example.test') == 'test'
    assert classify_origin({'source': 'itviec'}) == 'real'
