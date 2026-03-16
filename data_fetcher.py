"""
数据获取模块 - 适配 pc28.ai 接口版
"""
import aiohttp
import asyncio
from datetime import datetime
from typing import Optional, Dict, List
from logger import logger

class DataFetcher:
    def __init__(self):
        # 新的接口地址
        self.base_url = "https://pc28.ai/api/kj.json"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        self.last_period = None
        self.last_data = None
    
    async def fetch_latest_data(self) -> Optional[Dict]:
        """获取最新一期开奖数据"""
        try:
            # 请求最新的 1 条数据
            params = {'nbr': '1'}
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params, headers=self.headers, 
                                      timeout=aiohttp.ClientTimeout(total=10), ssl=False) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result and 'data' in result and len(result['data']) > 0:
                            # 拿到第一条数据进行解析
                            return self._parse_data(result['data'][0])
            return None
        except Exception as e:
            logger.error(f"获取最新数据异常: {str(e)}")
            return None
    
    def _parse_data(self, item: Dict) -> Dict:
        """根据 pc28.ai 的格式解析数据"""
        try:
            period = str(item.get('nbr', ''))
            num_str = item.get('num', '0')
            total = int(num_str)
            
            # 解析号码 (将 "6+3+7" 转换为列表 [6, 3, 7])
            raw_numbers = item.get('number', '')
            numbers = []
            if '+' in raw_numbers:
                nums_part = raw_numbers.split('+')
                for n in nums_part:
                    numbers.append(int(n.strip()))
            
            # 组合逻辑
            combination = item.get('combination', '')
            is_big = '大' in combination
            is_odd = '单' in combination
            
            return {
                'period': period,
                'numbers': numbers if len(numbers) == 3 else [0, 0, 0],
                'total': total,
                'is_big': is_big,
                'is_odd': is_odd,
                'open_time': f"{item.get('date')} {item.get('time')}",
                'raw_string': f"{raw_numbers}={total}"
            }
        except Exception as e:
            logger.error(f"解析数据异常: {str(e)}")
            return None
    
    async def fetch_history_data(self, count: int = 20) -> List[Dict]:
        """获取历史数据列表"""
        try:
            # 这里的 nbr 参数如果支持获取多条，可以填 count
            params = {'nbr': str(count)}
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params, headers=self.headers,
                                      timeout=aiohttp.ClientTimeout(total=15), ssl=False) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result and 'data' in result:
                            history = []
                            for item in result['data']:
                                parsed = self._parse_data(item)
                                if parsed:
                                    history.append(parsed)
                            return history
            return []
        except Exception as e:
            logger.error(f"获取历史数据异常: {str(e)}")
            return []
    
    async def check_new_data(self) -> Optional[Dict]:
        """检查新开奖"""
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
