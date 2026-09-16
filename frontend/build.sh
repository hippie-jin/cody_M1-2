#!/bin/sh
# Vercel Build Command로 실행된다.
# Vercel 프로젝트에 설정한 환경 변수 API_BASE_URL 값을 config.js에 주입해
# 프레임워크 없이도 "환경 변수로 API 서버 주소 설정"을 만족시킨다.
set -e

if [ -z "$API_BASE_URL" ]; then
  echo "경고: API_BASE_URL 환경 변수가 설정되지 않았습니다. config.js를 그대로 둡니다."
  exit 0
fi

sed "s|__API_BASE_URL__|$API_BASE_URL|g" config.template.js > config.js
echo "config.js 생성 완료: API_BASE_URL=$API_BASE_URL"
