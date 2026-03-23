#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests",
#     "beautifulsoup4",
#     "lxml",
# ]
# ///
"""
TPVL API 共用模組
從官網 __NEXT_DATA__ 取得資料（無公開 API）
"""

import json
import re
import requests
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Optional

# 快取設定
CACHE_DIR = Path('/tmp/tpvl_cache')
CACHE_TTL = timedelta(minutes=30)

BASE_URL = 'https://tpvl.tw'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
}

# 球隊 ID 對照
TEAM_IDS = {
    11380: '臺中連莊',
    11382: '台鋼天鷹',
    11383: '臺北伊斯特',
    11381: '桃園雲豹飛將',
}

# 球隊別名模糊匹配
TEAM_ALIASES = {
    '台中': '臺中連莊', '臺中': '臺中連莊', '連莊': '臺中連莊',
    '台鋼': '台鋼天鷹', '天鷹': '台鋼天鷹', 'tsg': '台鋼天鷹', 'skyhawks': '台鋼天鷹',
    '台北': '臺北伊斯特', '臺北': '臺北伊斯特', '伊斯特': '臺北伊斯特', 'east': '臺北伊斯特', 'power': '臺北伊斯特',
    '桃園': '桃園雲豹飛將', '雲豹': '桃園雲豹飛將', '飛將': '桃園雲豹飛將', 'leopards': '桃園雲豹飛將',
}

TST = timezone(timedelta(hours=8))


def _get_cache_path(key: str) -> Path:
    """取得快取檔案路徑"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f'{key}.json'


def _load_cache(key: str) -> Optional[dict]:
    """載入快取資料"""
    path = _get_cache_path(key)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        cached_at = datetime.fromisoformat(data.get('_cached_at', '2000-01-01'))
        if datetime.now() - cached_at < CACHE_TTL:
            return data
    except Exception:
        pass
    return None


def _save_cache(key: str, data: dict):
    """儲存快取資料"""
    data['_cached_at'] = datetime.now().isoformat()
    _get_cache_path(key).write_text(json.dumps(data, ensure_ascii=False))


def fetch_next_data(url: str, cache_key: str) -> dict:
    """
    從 TPVL 頁面提取 __NEXT_DATA__ JSON

    Args:
        url: 頁面 URL
        cache_key: 快取鍵值

    Returns:
        pageProps 內容
    """
    # 檢查快取
    cached = _load_cache(cache_key)
    if cached:
        return cached

    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()

    # 從 HTML 中提取 __NEXT_DATA__
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', resp.text)
    if not match:
        raise ValueError(f'無法從頁面提取 __NEXT_DATA__: {url}')

    data = json.loads(match.group(1))
    page_props = data.get('props', {}).get('pageProps', {})

    # 儲存快取
    _save_cache(cache_key, page_props)

    return page_props


def utc_to_local(utc_str: str) -> str:
    """UTC 時間轉台灣時間字串"""
    if not utc_str:
        return ''
    dt = datetime.fromisoformat(utc_str.replace('Z', '+00:00'))
    local_dt = dt.astimezone(TST)
    return local_dt.strftime('%Y-%m-%d %H:%M')


def resolve_team(name: str) -> Optional[str]:
    """模糊匹配球隊名稱"""
    name_lower = name.lower().strip()
    if name in TEAM_ALIASES.values():
        return name
    for alias, full_name in TEAM_ALIASES.items():
        if alias in name_lower or name_lower in alias:
            return full_name
    # 直接匹配
    for full_name in TEAM_ALIASES.values():
        if name in full_name or full_name in name:
            return full_name
    return None


def get_team_name(squad_id: int) -> str:
    """透過 squad ID 取得球隊名稱"""
    return TEAM_IDS.get(squad_id, f'未知球隊({squad_id})')


def parse_match(match: dict) -> dict:
    """將比賽資料轉換為統一格式"""
    result = {
        'id': match.get('id'),
        'code': match.get('code'),
        'status': match.get('status'),
        'date': '',
        'time': '',
        'venue': match.get('venue', ''),
        'home_team': get_team_name(match.get('homeSquadId')),
        'away_team': get_team_name(match.get('awaySquadId')),
        'home_score': None,
        'away_score': None,
        'home_sets': None,
        'away_sets': None,
        'round': match.get('round'),
    }

    # 時間轉換
    matched_at = match.get('matchedAt')
    if matched_at:
        local = utc_to_local(matched_at)
        if local:
            result['date'] = local[:10]
            result['time'] = local[11:16]

    # 比分（從 squadMatchResults 提取）
    smr = match.get('squadMatchResults', [])
    if smr:
        for r in smr:
            if r.get('squadId') == match.get('homeSquadId'):
                result['home_sets'] = r.get('wonRounds')
                result['away_sets'] = r.get('lostRounds')
                result['home_score'] = r.get('wonScore')
                result['away_score'] = r.get('lostScore')
                break

    return result


if __name__ == '__main__':
    # 測試：取得首頁資料
    print('測試首頁資料...')
    pp = fetch_next_data(BASE_URL, 'homepage')
    print(f'公告: {len(pp.get("announcements", []))} 則')
    print(f'已完賽: {len(pp.get("completedMatches", []))} 場')
    print(f'未來賽程: {len(pp.get("scheduleMatches", []))} 場')

    print('\n測試戰績頁...')
    rp = fetch_next_data(f'{BASE_URL}/record', 'record')
    teams = rp.get('resRankingsData', {}).get('teams_record', [])
    for t in teams:
        print(f"  {t['name']}: {t['wins']}W-{t['losses']}L ({t['winRate']})")

    print('\n✅ 所有測試通過')
