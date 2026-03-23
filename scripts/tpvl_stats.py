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
TPVL 球員數據查詢
⚠️ 目前 TPVL 官網球員數據頁面尚未上線（Coming Soon）
此腳本為預留接口，待官網開放後即可接入實際數據
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))
from _tpvl_api import resolve_team


def query_stats(
    year: Optional[int] = None,
    team: Optional[str] = None,
    category: Optional[str] = None,
    top: int = 10,
) -> list[dict]:
    """
    查詢球員數據（目前為佔位）

    Args:
        year: 年份過濾
        team: 球隊名過濾
        category: 統計類別（得分/攔網/發球/助攻/攔網/救球等）
        top: 顯示前 N 名

    Returns:
        空列表（目前無資料）
    """
    return []


def main():
    parser = argparse.ArgumentParser(
        description='TPVL 球員數據查詢（⚠️ 官網尚未開放）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
⚠️ 目前 TPVL 官網的球員數據頁面尚未上線（Coming Soon）
導航列中可見「球員數據」和「各場數據」但訪問回 404。
待官網開放後此腳本將接入實際數據。

預期支援的統計類別:
  - 得分 (Points)
  - 攔網 (Blocks)
  - 發球 (Serve)
  - 助攻 (Assists)
  - 攔網 (Blocks)
  - 救球 (Digs)

範例（未來可用）:
  uv run tpvl_stats.py --category 得分 --top 20
  uv run tpvl_stats.py --team 台鋼 --category 攔網
  uv run tpvl_stats.py --year 2025 --output text
        '''
    )

    parser.add_argument('--year', '-y', type=int, help='年份過濾')
    parser.add_argument('--team', '-t', type=str, help='球隊名過濾（支援別名）')
    parser.add_argument('--category', '-c', type=str, default='得分',
                        help='統計類別（得分/攔網/發球/助攻/救球）')
    parser.add_argument('--top', '-n', type=int, default=10, help='顯示前 N 名（預設 10）')
    parser.add_argument('--output', '-o', type=str, default='json', choices=['json', 'text'],
                        help='輸出格式（預設 json）')

    args = parser.parse_args()

    if args.team:
        resolved = resolve_team(args.team)
        if resolved and resolved != args.team:
            print(f'✅ 「{args.team}」→「{resolved}」', file=sys.stderr)
        elif not resolved:
            print(f'⚠️ 找不到球隊「{args.team}」', file=sys.stderr)

    print('⚠️ TPVL 官網球員數據頁面尚未開放（Coming Soon），目前無法查詢球員統計', file=sys.stderr)
    print('   導航列有「球員數據」和「各場數據」連結，但訪問回 404', file=sys.stderr)

    stats = query_stats(
        year=args.year,
        team=args.team,
        category=args.category,
        top=args.top,
    )

    if args.output == 'json':
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    else:
        print(f'\n🏅 TPVL 球員數據 — {args.category} Top {args.top}')
        print('   ⚠️ 官網尚未開放球員數據查詢功能')


if __name__ == '__main__':
    main()
