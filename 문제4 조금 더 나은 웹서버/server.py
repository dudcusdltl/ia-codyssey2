#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.request import urlopen
from urllib.error import URLError
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import csv

# ===== 설정 =====
HOST = '0.0.0.0'
PORT = 8080
WWW_DIR = Path('www')
IMG_DIR = WWW_DIR / 'images'
LOG_DIR = Path('logs')
ACCESS_LOG = LOG_DIR / 'access_log.csv'


def ensure_site_files() -> None:
    """초기 실행 시 정적 파일과 폴더를 준비한다."""
    WWW_DIR.mkdir(parents=True, exist_ok=True)
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # 간단한 SVG 이미지를 생성(표준 라이브러리만 사용)
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 300">'
        '<rect width="600" height="300" fill="#0b1020"/>'
        '<circle cx="90" cy="70" r="3" fill="#fff"/>'
        '<circle cx="140" cy="120" r="2" fill="#fff"/>'
        '<circle cx="300" cy="40" r="2.5" fill="#fff"/>'
        '<circle cx="420" cy="90" r="1.8" fill="#fff"/>'
        '<text x="50" y="190" fill="#7cf" font-size="36" font-family="monospace">'
        'SPACE PIRATES</text>'
        '<text x="50" y="230" fill="#9ef" font-size="18" font-family="monospace">'
        'Raid the stars, rule the trade lanes.</text>'
        '</svg>'
    )
    (IMG_DIR / 'space_pirates.svg').write_text(svg, encoding='utf-8')

    # index.html(요구사항: 우주 해적 소개 + 이미지)
    index_html = f"""<!doctype html>
<html lang='ko'>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <title>우주 해적 소개</title>
  <style>
    body {{
      margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont,
      'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Helvetica Neue', Arial, 'Noto Sans KR', sans-serif;
      color: #e8f0ff; background: #0a0f1a;
    }}
    header {{
      background: #0e1630; border-bottom: 1px solid #1b2a4a; padding: 24px;
    }}
    main {{ max-width: 880px; margin: 24px auto; padding: 0 16px; }}
    .card {{
      background: #0e1630; border: 1px solid #1b2a4a; border-radius: 14px;
      padding: 20px; box-shadow: 0 10px 30px rgba(0,0,0,.4);
    }}
    img {{ width: 100%; height: auto; border-radius: 10px; display: block; }}
    h1 {{ margin: 0 0 8px; font-size: 28px; }}
    p {{ line-height: 1.7; color: #cfe3ff; }}
    a.btn {{
      display: inline-block; margin-top: 14px; padding: 10px 14px; border-radius: 10px;
      border: 1px solid #2a3f6a; text-decoration: none; color: #cfe3ff;
    }}
    a.btn:hover {{ background: #132043; }}
    footer {{ text-align:center; padding: 32px; color:#92a7d9; }}
  </style>
</head>
<body>
  <header>
    <h1>우주 해적(Space Pirates)</h1>
    <p>별들 사이를 누비는 전설의 약탈자들 — 항로를 지배하고, 금지된 기술을 거래하며, 자유를 노래한다.</p>
  </header>
  <main>
    <div class='card'>
      <img src='images/space_pirates.svg' alt='Space Pirates Banner'>
      <h2>소개</h2>
      <p>
        우주 해적은 국가와 기업의 경계를 가볍게 넘나드는 집단으로, 누구의 통제도 받지 않는
        자유를 최고의 가치로 여깁니다. 그들의 배는 은하의 가장 어두운 항로에서 모습을 감추고,
        때로는 변칙 점프를 통해 추적을 피해 다닙니다.
      </p>
      <p>
        전리품은 꼭 물질만이 아닙니다. 네비게이션 루트, 암호화 키, 블랙박스 데이터처럼
        정보 그 자체가 최대의 전리품이 되죠. 전설적인 선장들은 계약과 배신 사이에서
        교묘한 균형을 잡으며, 우주 경제의 그림자 시장을 움직입니다.
      </p>
      <a class='btn' href='/stats'>요청 분석(Stats) 보기</a>
    </div>
  </main>
  <footer>© {datetime.now().year} Space Pirates • Made with Python http.server</footer>
</body>
</html>
"""
    (WWW_DIR / 'index.html').write_text(index_html, encoding='utf-8')

    # 접근 로그 헤더가 없다면 생성
    if not ACCESS_LOG.exists():
        with ACCESS_LOG.open('w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp_utc', 'client_ip', 'path', 'user_agent', 'geo'])


def lookup_geo(ip: str) -> str:
    """
    보너스: 클라이언트 IP를 간단히 위치 조회한다.
    - 표준 라이브러리(urllib)만 사용
    - 외부 네트워크 불가/실패 시 빈 문자열 반환
    - 사설망(예: 127.0.0.1, 10.x, 192.168.x)은 조회 의미가 적으므로 건너뜀
    """
    private_prefixes = ('127.', '10.', '192.168.', '172.16.', '172.17.', '172.18.', '172.19.',
                        '172.20.', '172.21.', '172.22.', '172.23.', '172.24.', '172.25.',
                        '172.26.', '172.27.', '172.28.', '172.29.', '172.30.', '172.31.')
    if ip.startswith(private_prefixes):
        return ''

    url = f'http://ip-api.com/json/{ip}?fields=status,country,regionName,city,timezone,query'
    try:
        with urlopen(url, timeout=2.5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get('status') == 'success':
                country = data.get('country') or ''
                region = data.get('regionName') or ''
                city = data.get('city') or ''
                tz = data.get('timezone') or ''
                parts = [p for p in [country, region, city, tz] if p]
                return ' / '.join(parts)
    except (URLError, TimeoutError, ValueError):
        pass
    return ''


def log_access(ip: str, path: str, user_agent: str, geo: str) -> None:
    """CSV 접근 로그에 한 줄을 추가한다."""
    ts_utc = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S%z')
    with ACCESS_LOG.open('a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([ts_utc, ip, path, user_agent, geo])


def render_stats_html() -> bytes:
    """간단한 요청 통계 HTML을 생성한다(최상위 경로별 히트 수)."""
    counts = {}
    total = 0
    if ACCESS_LOG.exists():
        with ACCESS_LOG.open('r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                path = row.get('path', '/')
                counts[path] = counts.get(path, 0) + 1
                total += 1

    rows = ''.join(
        f"<tr><td style='padding:8px;border-bottom:1px solid #1b2a4a'>{p}</td>"
        f"<td style='padding:8px;border-bottom:1px solid #1b2a4a;text-align:right'>{c}</td></tr>"
        for p, c in sorted(counts.items(), key=lambda x: (-x[1], x[0]))
    ) or "<tr><td colspan='2' style='padding:12px'>기록이 없습니다.</td></tr>"

    html = f"""<!doctype html>
<html lang='ko'>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <title>요청 분석</title>
</head>
<body style='margin:0;background:#0a0f1a;color:#e8f0ff;font-family:system-ui, -apple-system, Segoe UI, Roboto, Arial, "Noto Sans KR", sans-serif'>
  <header style='background:#0e1630;border-bottom:1px solid #1b2a4a;padding:24px'>
    <h1 style='margin:0'>요청 분석 (Stats)</h1>
    <p style='margin:6px 0 0;color:#cfe3ff'>총 요청 수: {total}</p>
    <a href='/' style='color:#9ef'>← 홈으로</a>
  </header>
  <main style='max-width:880px;margin:24px auto;padding:0 16px'>
    <div style='background:#0e1630;border:1px solid #1b2a4a;border-radius:14px;padding:20px'>
      <table style='width:100%;border-collapse:collapse'>
        <thead>
          <tr>
            <th style='text-align:left;padding:8px;border-bottom:1px solid #2a3f6a'>경로</th>
            <th style='text-align:right;padding:8px;border-bottom:1px solid #2a3f6a'>요청 수</th>
          </tr>
        </thead>
        <tbody>
          {rows}
        </tbody>
      </table>
      <p style='color:#92a7d9;margin-top:16px'>자세한 로그: <code>logs/access_log.csv</code></p>
    </div>
  </main>
</body>
</html>"""
    return html.encode('utf-8')


class SpacePirateHandler(SimpleHTTPRequestHandler):
    """요구사항 준수 + 간단 분석/지오로케이션 기능 포함 핸들러."""

    # SimpleHTTPRequestHandler의 기본 디렉터리 지정 (Py3.7+)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WWW_DIR), **kwargs)

    def do_GET(self) -> None:
        # 접속 정보
        client_ip = self.client_address[0]
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 서버 콘솔 출력(요구사항: 접속 시간, 클라이언트 IP)
        print(f'[접속] 시간={now}  IP={client_ip}  경로={self.path}')

        # 보너스: 간단 위치 조회(실패 시 빈 문자열)
        ua = self.headers.get('User-Agent', '')
        geo = lookup_geo(client_ip)

        # 분석 로그 저장
        try:
            log_access(client_ip, self.path, ua, geo)
        except Exception as e:
            # 로그 실패가 서비스에 영향 주지 않도록 무시
            print(f'[경고] 로그 기록 실패: {e}')

        # /stats 는 동적 HTML 생성
        if self.path == '/stats':
            body = render_stats_html()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # 루트는 index.html로 고정 매핑하여 확실히 200 응답
        if self.path in ('/', '/index.html'):
            index_file = WWW_DIR / 'index.html'
            if index_file.exists():
                data = index_file.read_bytes()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return

        # 그 외 정적 파일은 기본 처리
        super().do_GET()

    def log_message(self, fmt: str, *args) -> None:
        """
        기본 access 로그 형식을 간단히 조정.
        (경고 메시지 없이 실행되도록 불필요한 노이즈 최소화)
        """
        # 원하면 pass로 완전 무음 처리 가능. 여기서는 간단 출력 유지.
        print('[서버]', fmt % args)


def run_server() -> None:
    ensure_site_files()
    server_address = (HOST, PORT)
    httpd = HTTPServer(server_address, SpacePirateHandler)
    print(f'🌌 Space Pirates server running at http://localhost:{PORT}')
    print(f'문서 루트: {WWW_DIR.resolve()}  |  접근 로그: {ACCESS_LOG.resolve()}')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\n서버 종료를 요청했습니다. 안녕히 계세요.')
    finally:
        httpd.server_close()


if __name__ == '__main__':
    run_server()
