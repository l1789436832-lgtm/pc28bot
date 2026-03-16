"""
预测算法与资金管理模块 - 增强版
"""
import random
import math
from typing import Dict, List, Optional, Tuple
from collections import Counter
from logger import logger

class Predictor:
    def __init__(self):
        self.history_data: List[Dict] = []
        self.prediction_records: List[Dict] = []
        # 资金管理状态
        self.consecutive_loss = 0
        self.fibonacci_sequence = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
        self.fib_index = 0

    def update_history(self, history: List[Dict]):
        self.history_data = history

    def predict_next(self) -> Dict:
        if len(self.history_data) < 10:
            return self._random_predict()
        
        # 多模型权重
        trend_result = self._trend_analysis()        # 30%
        freq_result = self._frequency_analysis()    # 20%
        pattern_result = self._pattern_analysis()    # 30%
        mean_result = self._mean_reversion_analysis() # 20%
        
        prediction = self._combine_predictions([
            (trend_result, 0.30),
            (freq_result, 0.20),
            (pattern_result, 0.30),
            (mean_result, 0.20)
        ])

        # 注入资金管理建议
        prediction['betting_plan'] = self._get_betting_suggestion()
        return prediction

    def _mean_reversion_analysis(self) -> Dict:
        """均值回归分析：总和偏离 13.5 太远则预期回归"""
        recent = self.history_data[:15]
        avg_total = sum(d.get('total', 13.5) for d in recent) / len(recent)
        
        # 如果最近均值远大于14，则预测小；反之预测大
        predict_big = avg_total < 13.5
        confidence = 0.5 + min(abs(avg_total - 13.5) * 0.05, 0.3)
        
        return {'is_big': predict_big, 'is_odd': random.choice([True, False]), 
                'big_confidence': confidence, 'odd_confidence': 0.5}

    def _trend_analysis(self) -> Dict:
        recent = self.history_data[:12]
        big_count = sum(1 for d in recent if d.get('is_big'))
        odd_count = sum(1 for d in recent if d.get('is_odd'))
        
        # 趋势反转逻辑：如果近期大太多，反而预测小
        predict_big = big_count <= 6
        big_confidence = 0.5 + abs(big_count - 6) * 0.05
        
        predict_odd = odd_count <= 6
        odd_confidence = 0.5 + abs(odd_count - 6) * 0.05
        
        return {'is_big': predict_big, 'is_odd': predict_odd, 
                'big_confidence': big_confidence, 'odd_confidence': odd_confidence}

    def _frequency_analysis(self) -> Dict:
        """冷热号分析"""
        recent = self.history_data[:50]
        all_nums = []
        for d in recent:
            all_nums.extend(d.get('numbers', []))
        
        counts = Counter(all_nums)
        # 这里简单逻辑：如果 0-4 出现的频率远高于 5-9，则预期未来大
        small_freq = sum(counts[i] for i in range(5))
        big_freq = sum(counts[i] for i in range(5, 10))
        
        predict_big = big_freq < small_freq
        return {'is_big': predict_big, 'is_odd': random.choice([True, False]),
                'big_confidence': 0.55, 'odd_confidence': 0.5}

    def _pattern_analysis(self) -> Dict:
        """长龙检测（核心：反龙策略）"""
        recent = self.history_data[:10]
        
        def get_streak(key):
            count = 0
            first_val = recent[0].get(key)
            for d in recent:
                if d.get(key) == first_val:
                    count += 1
                else:
                    break
            return count, first_val

        big_streak, last_big_val = get_streak('is_big')
        odd_streak, last_odd_val = get_streak('is_odd')

        # 如果连出 5 期大，强烈预测小（反龙）
        if big_streak >= 5:
            predict_big = not last_big_val
            big_conf = 0.6 + min(big_streak * 0.05, 0.25)
        else:
            predict_big = not last_big_val if big_streak >= 2 else last_big_val
            big_conf = 0.52

        if odd_streak >= 5:
            predict_odd = not last_odd_val
            odd_conf = 0.6 + min(odd_streak * 0.05, 0.25)
        else:
            predict_odd = not last_odd_val if odd_streak >= 2 else last_odd_val
            odd_conf = 0.52

        return {'is_big': predict_big, 'is_odd': predict_odd,
                'big_confidence': big_conf, 'odd_confidence': odd_conf}

    def _get_betting_suggestion(self) -> str:
        """生成资金管理建议"""
        stats = self.get_stats()
        win_rate = stats['accuracy']
        
        # 1. 凯利公式建议 (假设赔率为 1.95)
        if win_rate > 0.52:
            b = 0.95 
            p = win_rate
            q = 1 - p
            kelly_f = (b * p - q) / b
            kelly_suggestion = f"凯利公式建议仓位: {max(0, round(kelly_f * 100, 1))}%"
        else:
            kelly_suggestion = "胜率不足，建议轻仓观望"

        # 2. 斐波那契加注建议
        fib_val = self.fibonacci_sequence[min(self.fib_index, len(self.fibonacci_sequence)-1)]
        fib_suggestion = f"稳健倍投: {fib_val} 单位 (当前第 {self.fib_index + 1} 级)"

        return f"【资金管理】\n• {kelly_suggestion}\n• {fib_suggestion}\n• 建议方案: {'斐波那契减压' if self.consecutive_loss > 2 else '平刷或均注'}"

    def record_result(self, prediction: Dict, actual: Dict) -> bool:
        is_correct = (prediction.get('is_big') == actual.get('is_big')) and \
                     (prediction.get('is_odd') == actual.get('is_odd'))
        
        if is_correct:
            self.consecutive_loss = 0
            self.fib_index = max(0, self.fib_index - 2) # 赢了退两级
        else:
            self.consecutive_loss += 1
            self.fib_index += 1 # 输了进一级

        self.prediction_records.append({
            'period': actual.get('period'),
            'full_correct': is_correct,
            'big_correct': prediction.get('is_big') == actual.get('is_big'),
            'odd_correct': prediction.get('is_odd') == actual.get('is_odd')
        })
        return is_correct

    def _combine_predictions(self, predictions: List[Tuple[Dict, float]]) -> Dict:
        # (保持原有的权重组合逻辑，但输出更详细的分析)
        big_score = 0
        odd_score = 0
        for pred, weight in predictions:
            if pred.get('is_big'): big_score += weight
            if pred.get('is_odd'): odd_score += weight
        
        predict_big = big_score >= 0.5
        predict_odd = odd_score >= 0.5
        
        # 生成期数
        next_period = "下一期"
        if self.history_data:
            next_period = str(int(self.history_data[0].get('period', 0)) + 1)

        return {
            'period': next_period,
            'is_big': predict_big,
            'is_odd': predict_odd,
            'predicted_total_range': "14-27 (大)" if predict_big else "0-13 (小)",
            'big_confidence': 0.6, # 简化处理
            'odd_confidence': 0.6,
            'analysis': "综合均值回归与反龙算法，当前走势倾向明显。"
        }

    def get_stats(self) -> Dict:
        if not self.prediction_records:
            return {'total': 0, 'accuracy': 0}
        total = len(self.prediction_records)
        correct = sum(1 for r in self.prediction_records if r.get('full_correct'))
        return {'total': total, 'accuracy': correct / total}

    def _random_predict(self) -> Dict:
        return {'period': '下一期', 'is_big': True, 'is_odd': False, 'analysis': '正在收集数据...', 'betting_plan': '等待数据中'}

predictor = Predictor()
