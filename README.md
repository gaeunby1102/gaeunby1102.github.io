# gaeunby1102.github.io

Gaeun Byeon의 개인 홈페이지 (순수 HTML/CSS, 빌드 도구 없음).

## 구조
- `index.html` — About (홈)
- `projects.html` — 프로젝트 소개
- `posters.html` — 학회 포스터 갤러리
- `notes.html` — 공부 노트 목록
- `notes/` — 개별 노트 HTML (`_template.html` 복사해서 추가)
- `assets/css/style.css` — 스타일 (라이트/다크 자동)
- `assets/posters/`, `assets/img/` — 이미지

## 로컬 미리보기
```bash
cd ~/gaeunby1102.github.io
python3 -m http.server 8000
# 브라우저에서 http://localhost:8000
```

## 콘텐츠 추가
- **프로젝트**: `projects.html`의 `<li>` 편집
- **포스터**: 이미지를 `assets/posters/`에 넣고 `posters.html`에 `<figure>` 추가
- **노트**: `notes/_template.html` 복사 → 내용 작성 → `notes.html` 목록에 링크

## 배포
GitHub `gaeunby1102.github.io` 레포에 push하면 자동으로
https://gaeunby1102.github.io 에 게시됩니다.
