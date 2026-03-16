"""
预测算法模块
"""
import random
from typing import Dict, List, Optional, Tuple
from collections import Counter
from logger import logger


class Predictor:
    def __init__(self):
        self.history_data: List[Dict] = []
        self.prediction_records: List[Dict] = []
        self.correct_count = 0
        self.total_count = 0
    
    def update_history(self, history: List[Dict]):
        self.history_data = history
    
    def predict_next(self) -> Dict:
        if len(self.history_data) < 5:
            return self._random_predict()
        
        trend_result = self._trend_analysis()
        freq_result = self._frequency_analysis()
        pattern_result = self._pattern_analysis()
        
        return self._combine_predictions([
            (trend_result, 0.35),
            (freq_result, 0.35),
            (pattern_result, 0.30)
        ])
    
    def _trend_analysis(self) -> Dict:
        recent = self.history_data[:10]
        big_count = sum(1 for d in recent if d.get('is_big'))
        odd_count = sum(1 for d in recent if d.get('is_odd'))
        big_ratio = big_count / len(recent)
        odd_ratio = odd_count / len(recent)
        
        if big_ratio > 0.6:
            predict_big = False
            big_confidence = 0.5 + (big_ratio - 0.5) * 0.3
        elif big_ratio < 0.4:
            predict_big = True
            big_confidence = 0.5 + (0.5 - big_ratio) * 0.3
        else:
            predict_big = big_count <= 5
            big_confidence = 0.5
        
        if odd_ratio > 0.6:
            predict_odd = False
            odd_confidence = 0.5 + (odd_ratio - 0.5) * 0.3
        elif odd_ratio < 0.4:
            predict_odd = True
            odd_confidence = 0.5 + (0.5 - odd_ratio) * 0.3
        else:
            predict_odd = odd_count <= 5
            odd_confidence = 0.5
        
        return {'is_big': predict_big, 'is_odd': predict_odd, 
                'big_confidence': big_confidence, 'odd_confidence': odd_confidence}
    
    def _frequency_analysis(self) -> Dict:
        recent = self.history_data[:30]
        totals = [d.get('total', 0) for d in recent if d.get('total')]
        if not totals:
            return self._random_predict()
        
        big_sum = sum(1 for t in totals if t >= 14)
        small_sum = len(totals) - big_sum
        odd_sum = sum(1 for t in totals if t % 2 == 1)
        even_sum = len(totals) - odd_sum
        
        predict_big = big_sum < small_sum
        predict_odd = odd_sum < even_sum
        big_diff = abs(big_sum - small_sum) / len(totals)
        odd_diff = abs(odd_sum - even_sum) / len(totals)
        
        return {'is_big': predict_big, 'is_odd': predict_odd,
                'big_confidence': 0.5 + big_diff * 0.2, 'odd_confidence': 0.5 + odd_diff * 0.2}
    
    def _pattern_analysis(self) -> Dict:
        recent = self.history_data[:20]
        if len(recent) < 3:
            return self._random_predict()
        
        consecutive_big = 0
        consecutive_small = 0
        for d in recent:
            if d.get('is_big'):
                consecutive_big += 1
                if consecutive_small > 0:
                    break
            else:
                consecutive_small += 1
                if consecutive_big > 0:
                    break
        
        consecutive_odd = 0
        consecutive_even = 0
        for d in recent:
            if d.get('is_odd'):
                consecutive_odd += 1
                if consecutive_even > 0:
                    break
            else:
                consecutive_even += 1
                if consecutive_odd > 0:
                    break
        
        if consecutive_big >= 3:
            predict_big = False
            big_confidence = 0.5 + min(consecutive_big - 2, 3) * 0.1
        elif consecutive_small >= 3:
            predict_big = True
            big_confidence = 0.5 + min(consecutive_small - 2, 3) * 0.1
        else:
            predict_big = consecutive_big < consecutive_small
            big_confidence = 0.5
        
        if consecutive_odd >= 3:
            predict_odd = False
            odd_confidence = 0.5 + min(consecutive_odd - 2, 3) * 0.1
        elif consecutive_even >= 3:
            predict_odd = True
            odd_confidence = 0.5 + min(consecutive_even - 2, 3) * 0.1
        else:
            predict_odd = consecutive_odd < consecutive_even
            odd_confidence = 0.5
        
        return {'is_big': predict_big, 'is_odd': predict_odd,
                'big_confidence': big_confidence, 'odd_confidence': odd_confidence}
    
    def _combine_predictions(self, predictions: List[Tuple[Dict, float]]) -> Dict:
        big_score = 0
        odd_score = 0
        big_conf_sum = 0
        odd_conf_sum = 0
        
        for pred, weight in predictions:
            if pred.get('is_big'):
                big_score += weight
            big_conf_sum += pred.get('big_confidence', 0.5) * weight
            if pred.get('is_odd'):
                odd_score += weight
            odd_conf_sum += pred.get('odd_confidence', 0.5) * weight
        
        total_weight = sum(w for _, w in predictions)
        predict_big = big_score > total_weight / 2
        predict_odd = odd_score > total_weight / 2
        big_confidence = big_conf_sum / total_weight
        odd_confidence = odd_conf_sum / total_weight
        
        next_period = ""
        if self.history_data:
            try:
                current = int(self.history_data[0].get('period', 0))
                next_period = str(current + 1)
            except:
                next_period = "下一期"
        
        predicted_total = "14-27 (大)" if predict_big else "0-13 (小)"
        analysis = self._generate_analysis(predict_big, predict_odd, big_confidence, odd_confidence)
        
        return {
            'period': next_period, 'is_big': predict_big, 'is_odd': predict_odd,
            'big_confidence': min(big_confidence, 0.85), 'odd_confidence': min(odd_confidence, 0.85),
            'predicted_total_range': predicted_total, 'analysis': analysis
        }
    
    def _generate_analysis(self, is_big, is_odd, big_conf, odd_conf) -> str:
        analysis = []
        if big_conf > 0.7:
            analysis.append(f"大小趋势明显，{'大' if is_big else '小'}的概率较高")
        elif big_conf > 0.6:
            analysis.append(f"大小走势偏向{'大' if is_big else '小'}")
        else:
            analysis.append("大小走势不明朗，建议谨慎")
        
        if odd_conf > 0.7:
            analysis.append(f"单双趋势明显，{'单' if is_odd else '双'}的概率较高")
        elif odd_conf > 0.6:
            analysis.append(f"单双走势偏向{'单' if is_odd else '双'}")
        else:
            analysis.append("单双走势不明朗，建议观望")
        return "\n".join(analysis)
    
    def _random_predict(self) -> Dict:
        return {
            'period': '下一期', 'is_big': random.choice([True, False]),
            'is_odd': random.choice([True, False]), 'big_confidence': 0.5,
            'odd_confidence': 0.5, 'predicted_total_range': '0-27',
            'analysis': '历史数据不足，随机预测'
        }
    
    def record_result(self, prediction: Dict, actual: Dict) -> bool:
        self.total_count += 1
        big_correct = prediction.get('is_big') == actual.get('is_big')
        odd_correct = prediction.get('is_odd') == actual.get('is_odd')
        if big_correct and odd_correct:
            self.correct_count += 1
        
        self.prediction_records.append({
            'period': actual.get('period'), 'big_correct': big_correct,
            'odd_correct': odd_correct, 'full_correct': big_correct and odd_correct
        })
        if len(self.prediction_records) > 100:
            self.prediction_records = self.prediction_records[-100:]
        return big_correct and odd_correct
    
    def get_stats(self) -> Dict:
        if not self.prediction_records:
            return {'total': 0, 'correct': 0, 'accuracy': 0, 'big_accuracy': 0, 'odd_accuracy': 0}
        
        total = len(self.prediction_records)
        correct = sum(1 for r in self.prediction_records if r.get('full_correct'))
        big_correct = sum(1 for r in self.prediction_records if r.get('big_correct'))
        odd_correct = sum(1 for r in self.prediction_records if r.get('odd_correct'))
        
        return {
            'total': total, 'correct': correct,
            'accuracy': correct / total if total > 0 else 0,
            'big_accuracy': big_correct / total if total > 0 else 0,
            'odd_accuracy': odd_correct / total if total > 0 else 0
        }


predictor = Predictor()
