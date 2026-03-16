"""
数据获取模块
"""
import aiohttp
import asyncio
from datetime import datetime
from typing import Optional, Dict, List
from logger import logger


class DataFetcher:
    def __init__(self):
        self.base_url = "https://dd28yc.com/data/get/getForecastByType"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Referer': 'https://dd28yc.com/',
            'Origin': 'https://dd28yc.com'
        }
        self.last_period = None
        self.last_data = None
    
    async def fetch_latest_data(self) -> Optional[Dict]:
        try:
            params = {'game': 'jnd28', 'type': 'zh', 'sf': '1'}
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params, headers=self.headers, 
                                      timeout=aiohttp.ClientTimeout(total=10), ssl=False) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result and 'data' in result and len(result['data']) > 0:
                            for item in result['data']:
                                if item.get('kjcode') and item['kjcode'] != '---':
                                    return self._parse_data(item)
                        return None
                    return None
        except Exception as e:
            logger.error(f"获取数据异常: {str(e)}")
            return None
    
    def _parse_data(self, item: Dict) -> Dict:
        try:
            period = str(item.get('qishu', ''))
            kjcodestr = item.get('kjcodestr', '')
            numbers = []
            total = 0
            
            if kjcodestr and '=' in kjcodestr:
                parts = kjcodestr.split('=')
                nums_part = parts[0]
                total = int(parts[1]) if len(parts) > 1 else 0
                nums = nums_part.split('+')
                for n in nums:
                    try:
                        numbers.append(int(n.strip()))
                    except:
                        pass
            
            if not total and item.get('kjcode'):
                try:
                    total = int(item['kjcode'])
                except:
                    pass
            
            dx = item.get('dx', '')
            ds = item.get('ds', '')
            is_big = '大' in dx if dx else (total >= 14 if total else None)
            is_odd = '单' in ds if ds else (total % 2 == 1 if total else None)
            
            return {
                'period': period,
                'numbers': numbers if len(numbers) == 3 else [0, 0, 0],
                'total': total,
                'is_big': is_big,
                'is_odd': is_odd,
                'open_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'raw_string': kjcodestr
            }
        except Exception as e:
            logger.error(f"解析数据异常: {str(e)}")
            return None
    
    async def fetch_history_data(self, count: int = 20) -> List[Dict]:
        try:
            params = {'game': 'jnd28', 'type': 'zh', 'sf': '1'}
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params, headers=self.headers,
                                      timeout=aiohttp.ClientTimeout(total=15), ssl=False) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result and 'data' in result:
                            history = []
                            for item in result['data']:
                                if item.get('kjcode') and item['kjcode'] != '---':
                                    parsed = self._parse_data(item)
                                    if parsed:
                                        history.append(parsed)
                                    if len(history) >= count:
                                        break
                            return history
                    return []
        except Exception as e:
            logger.error(f"获取历史数据异常: {str(e)}")
            return []
    
    async def check_new_data(self) -> Optional[Dict]:
        data = await self.fetch_latest_data()
        if data and data.get('period'):
            if self.last_period is None:
                self.last_period = data['period']
                self.last_data = data
                return None
            if data['period'] != self.last_period:
                logger.info(f"发现新开奖: {self.last_period} -> {data['period']}")
                self.last_period = data['period']
                self.last_data = data
                return data
        return None


data_fetcher = DataFetcher()
