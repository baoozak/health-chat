"""
健康分析服务
负责健康数据的智能分析和报告生成
"""
from typing import List, Dict, Optional
import logging
import json
import re
from datetime import datetime
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)

class HealthAnalysisService:
    """健康分析服务
    
    主要职责：
    1. generate_health_analysis: 主要的健康分析生成方法，调用AI获取三个子评分
    2. calculate_average_score: 计算三个子评分的平均值（主要评分逻辑）
    """
    
    def __init__(self):
        """初始化健康分析服务"""
        self.ai_service = ai_service
    
    def calculate_average_score(self, score_data: Dict) -> int:
        """
        计算三个子评分的平均值
        
        Args:
            score_data: 包含physical, mental, lifestyle评分的字典
            
        Returns:
            平均评分 (0-100)
        """
        try:
            physical = score_data.get("physical", 75)
            mental = score_data.get("mental", 75)
            lifestyle = score_data.get("lifestyle", 75)
            
            # 计算三个子项的平均值作为综合评分
            avg_score = (physical + mental + lifestyle) / 3
            return int(avg_score)
            
        except Exception as e:
            logger.error(f"计算平均评分失败: {str(e)}")
            return 75  # 默认评分
    
    async def generate_health_analysis(self, health_data: Dict) -> Dict:
        """
        使用AI生成健康分析报告
        
        Args:
            health_data: 提取的健康数据
            
        Returns:
            健康分析结果
        """
        try:
            # 准备AI分析的输入数据
            conversation_summary = self._prepare_conversation_summary(health_data)
            
            # 构造AI提示词 - 让AI根据完整会话记录生成三项详细评分
            prompt = f"""你是专业的健康数据分析师。请基于以下用户的历史健康咨询数据，生成全面的健康状况评估报告。

用户历史数据摘要:
- 会话数量: {health_data.get('total_conversations', 0)}
- 消息总数: {health_data.get('total_messages', 0)}
- 文件上传: {health_data.get('file_uploads', 0)}
- 时间范围: {health_data.get('date_range', {}).get('start', '未知')} 至 {health_data.get('date_range', {}).get('end', '未知')}

用户主要咨询内容摘要:
{conversation_summary}

请按以下JSON结构分析（务必返回有效的JSON格式）:

{{
  "health_score": {{
    "physical": 85,     # 身体健康评分(0-100)，基于用户咨询的身体相关问題
    "mental": 80,       # 心理健康评分(0-100)，基于用户表达的情绪和心理状态
    "lifestyle": 75,    # 生活方式评分(0-100)，基于用户的生活习惯描述
    "overall": 80     # 综合评分，取上面三项的平均值
  }},
  "risk_assessment": {{
    "high_risk": [],  # 基于用户实际数据，没有就留空，使用中文描述
    "medium_risk": [], # 基于用户实际数据，没有就留空，使用中文描述
    "low_risk": []     # 基于用户实际数据，没有就留空，使用中文描述
  }},
  "trends": {{
    "weight": {{"direction": "stable", "change": 0, "period": "30天"}},
    "exercise": {{"direction": "up", "change": 15, "period": "30天"}}
  }},
  "recommendations": {{
    "diet": [],      # 基于用户实际数据，没有就留空，使用中文描述
    "exercise": [],  # 基于用户实际数据，没有就留空，使用中文描述
    "lifestyle": [], # 基于用户实际数据，没有就留空，使用中文描述
    "medical": []     # 基于用户实际数据，没有就留空，使用中文描述
  }}
}}

评分指导原则:

**关键评分原则**:
1. **不要给"虚高"分数** - 除非有明确的积极证据，否则默认使用较低的评分
2. 只要用户提到任何健康问题（如失眠、疲劳、压力大），相应维度就不应超过 70 分
3. 如果用户没有提供足够信息，应给予中等偏低评分（75分左右），而不是高分
4. 90分以上的评分应该极其罕见，只有在用户明确表示各方面都非常好的情况下才给出

**身体健康评分**: 基于用户提到的身体症状、疾病史、体检数据等
- 85-100分: 身体状况良好，无明显健康问题
- 70-84分: 身体基本健康，可能有轻微问题
- 60-69分: 身体存在一些问题，需要关注
- 0-59分: 身体有明显健康问题，建议就医

**心理健康评分**: 基于用户表达的情绪状态、压力水平、睡眠质量等
- 85-100分: 心理状态良好，情绪稳定
- 70-84分: 心理状态一般，偶有情绪波动
- 60-69分: 存在心理压力或情绪问题
- 0-59分: 心理健康需要重点关注

**生活方式评分**: 基于用户的生活习惯、作息规律、运动情况等
- 85-100分: 生活方式健康，作息规律
- 70-84分: 生活方式基本健康，有改善空间
- 60-69分: 生活方式不够健康，需要调整
- 0-59分: 生活方式不健康，急需改善

重要提醒:
- **必须严格基于用户实际提供的数据进行分析，绝不能编造任何健康信息**
- 如果用户数据不足以得出某方面结论，相应字段必须留空[]
- **所有分析结果必须使用中文，包括风险项目、建议和趋势描述**
- 这是健康管理建议，不是医疗诊断
- 发现严重异常时，务必建议就医
- 不推荐具体药物
- 请只返回JSON，不要有其他文字说明
"""
            
            # 调用AI服务（使用LangChain的invoke获取完整响应）
            logger.info("开始调用AI进行健康分析...")
            from langchain_core.messages import HumanMessage
            ai_response_msg = self.ai_service.llm.invoke(prompt)
            ai_response = ai_response_msg.content
            
            logger.info(f"AI分析完成，响应长度: {len(ai_response)}")
            
            # 解析AI返回的JSON
            analysis_result = self._parse_ai_response(ai_response)
            
            # 计算健康评分 - 让AI根据会话记录生成三项详细评分
            if "health_score" not in analysis_result or not analysis_result["health_score"]:
                # 使用AI生成的评分，如果没有则使用默认值
                analysis_result["health_score"] = {
                    "overall": 75,  # 临时值，后面会重新计算
                    "physical": 75,
                    "mental": 75,
                    "lifestyle": 75
                }
            
            # 确保综合评分是三个子项的平均值（无论AI是否返回了评分）
            existing_scores = analysis_result["health_score"]
            if isinstance(existing_scores, dict):
                # 使用专门的工具方法计算平均值
                existing_scores["overall"] = self.calculate_average_score(existing_scores)
            
            # 生成综合分析文字
            ai_comprehensive_analysis = self._generate_comprehensive_analysis(analysis_result, conversation_summary)
            
            # 添加综合分析
            analysis_result["ai_comprehensive_analysis"] = ai_comprehensive_analysis
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"生成健康分析失败: {str(e)}")
            # 返回默认分析结果
            return self._get_default_analysis()
    
    def _prepare_conversation_summary(self, health_data: Dict) -> str:
        """
        准备会话摘要
        
        Args:
            health_data: 健康数据
            
        Returns:
            会话摘要文本
        """
        try:
            summary_parts = []
            
            # 提取用户消息的关键内容（最多前10条）
            user_messages = health_data.get("user_messages", [])[:10]
            for i, msg in enumerate(user_messages, 1):
                content = msg.get("content", "")[:200]  # 限制长度
                summary_parts.append(f"{i}. {content}")
            
            return "\n".join(summary_parts) if summary_parts else "暂无详细咨询记录"
            
        except Exception as e:
            logger.error(f"准备会话摘要失败: {str(e)}")
            return "数据处理出错"
    
    def _parse_ai_response(self, response: str) -> Dict:
        """
        解析AI返回的JSON响应
        
        Args:
            response: AI响应文本
            
        Returns:
            解析后的字典
        """
        try:
            # 尝试直接解析
            return json.loads(response)
        except json.JSONDecodeError:
            # 如果失败，尝试提取JSON部分
            try:
                # 查找JSON代码块
                json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))
                
                # 查找花括号包裹的内容
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))
                
                logger.error("无法从AI响应中提取JSON")
                return self._get_default_analysis()
                
            except Exception as e:
                logger.error(f"解析AI响应失败: {str(e)}")
                return self._get_default_analysis()
    
    def _get_score_level(self, score: int) -> str:
        """
        根据评分获取等级描述（与前端统一标准）
        
        Args:
            score: 评分（0-100）
            
        Returns:
            等级描述
        """
        if score >= 85:
            return "优秀"
        elif score >= 70:
            return "良好"
        elif score >= 60:
            return "一般"
        else:
            return "需改善"

    def _generate_comprehensive_analysis(self, analysis_result: Dict, conversation_summary: str) -> str:
        """
        生成综合分析文字（支持Markdown格式）
        
        Args:
            analysis_result: AI分析结果
            conversation_summary: 会话摘要
            
        Returns:
            综合分析文字（Markdown格式）
        """
        try:
            health_score = analysis_result.get("health_score", {})
            risk_assessment = analysis_result.get("risk_assessment", {})
            recommendations = analysis_result.get("recommendations", {})
            
            # 获取健康评分
            overall_score = health_score.get("overall", 75)
            physical_score = health_score.get("physical", 75)
            mental_score = health_score.get("mental", 75)
            lifestyle_score = health_score.get("lifestyle", 75)
            
            # 分析风险情况
            high_risk_count = len(risk_assessment.get("high_risk", []))
            medium_risk_count = len(risk_assessment.get("medium_risk", []))
            low_risk_count = len(risk_assessment.get("low_risk", []))
            
            # 构建Markdown格式的分析文本
            analysis_parts = []
            
            # 标题和总体评价
            analysis_parts.append("## 📊 健康状况总览")
            
            # 总体评价 - 统一评分标准（与前端保持一致）
            if overall_score >= 85:
                analysis_parts.append(f"### ✅ 整体评价：优秀（{overall_score}分）")
                analysis_parts.append("根据您的健康数据分析，您的整体健康状况优秀，请继续保持良好的生活习惯。")
            elif overall_score >= 70:
                analysis_parts.append(f"### 👍 整体评价：良好（{overall_score}分）")
                analysis_parts.append("根据您的健康数据分析，您的整体健康状况良好，在保持现有状态的基础上有小幅提升空间。")
            elif overall_score >= 60:
                analysis_parts.append(f"### ⚠️ 整体评价：一般（{overall_score}分）")
                analysis_parts.append("根据您的健康数据分析，您的整体健康状况一般，有改善空间，建议关注以上方面的健康建议。")
            else:
                analysis_parts.append(f"### 🚨 整体评价：需改善（{overall_score}分）")
                analysis_parts.append("根据您的健康数据分析，您的健康状况需要重点关注和改善，建议采取积极的健康管理措施，必要时咨询医生意见。")
            
            # 详细评分展示
            analysis_parts.append("\n## 📈 详细评分")
            analysis_parts.append("| 评估维度 | 得分 | 等级 |")
            analysis_parts.append("|---------|------|------|")
            analysis_parts.append(f"| 身体健康 | {physical_score}分 | {self._get_score_level(physical_score)} |")
            analysis_parts.append(f"| 心理健康 | {mental_score}分 | {self._get_score_level(mental_score)} |")
            analysis_parts.append(f"| 生活方式 | {lifestyle_score}分 | {self._get_score_level(lifestyle_score)} |")
            analysis_parts.append(f"| **综合评分** | **{overall_score}分** | **{self._get_score_level(overall_score)}** |")
            
            # 风险分析
            analysis_parts.append("\n## ⚠️ 风险评估")
            risk_factors = []
            if analysis_result.get("risk_assessment", {}).get("high_risk"):
                risk_factors.extend(analysis_result["risk_assessment"]["high_risk"])
            if analysis_result.get("risk_assessment", {}).get("medium_risk"):
                risk_factors.extend(analysis_result["risk_assessment"]["medium_risk"])
            
            if risk_factors:
                if len(risk_factors) <= 3:
                    analysis_parts.append(f"当前发现的健康风险包括：")
                    for risk in risk_factors:
                        analysis_parts.append(f"- **{risk}**")
                    analysis_parts.append("建议定期监测相关指标，必要时咨询医生。")
                else:
                    analysis_parts.append(f"当前发现**{len(risk_factors)}项**健康风险因素：")
                    for risk in risk_factors[:3]:
                        analysis_parts.append(f"- **{risk}**")
                    analysis_parts.append(f"以及其他{len(risk_factors) - 3}项风险因素。")
                    analysis_parts.append("**建议及时就医进行专业评估**，制定针对性的健康管理计划。")
            else:
                # 如果没有足够数据，明确说明而不是编造
                if conversation_summary == "暂无详细咨询记录":
                    analysis_parts.append("目前缺乏足够的健康咨询数据来进行详细的风险评估。")
                    analysis_parts.append("💡 **建议**：多与AI助手交流健康问题，以便获得更准确的健康评估。")
                else:
                    analysis_parts.append("✅ 目前暂未发现明显的健康风险因素。")
                    analysis_parts.append("请继续保持良好的生活习惯，定期进行健康监测。")
            
            # 风险等级统计
            if high_risk_count > 0 or medium_risk_count > 0 or low_risk_count > 0:
                analysis_parts.append(f"\n**风险统计**：")
                if high_risk_count > 0:
                    analysis_parts.append(f"- 🔴 **高风险**：{high_risk_count}项")
                if medium_risk_count > 0:
                    analysis_parts.append(f"- 🟡 **中风险**：{medium_risk_count}项")
                if low_risk_count > 0:
                    analysis_parts.append(f"- 🟢 **低风险**：{low_risk_count}项")
            
            # 建议总结
            total_recommendations = 0
            for category in recommendations.values():
                total_recommendations += len(category)
            
            if total_recommendations > 0:
                analysis_parts.append(f"\n## 💡 个性化建议")
                analysis_parts.append(f"系统为您提供了**{total_recommendations}条**个性化健康建议，涵盖以下方面：")
                
                if recommendations.get("diet") and len(recommendations["diet"]) > 0:
                    analysis_parts.append(f"- 🥗 **饮食建议**：{len(recommendations['diet'])}条")
                if recommendations.get("exercise") and len(recommendations["exercise"]) > 0:
                    analysis_parts.append(f"- 🏃 **运动建议**：{len(recommendations['exercise'])}条")
                if recommendations.get("lifestyle") and len(recommendations["lifestyle"]) > 0:
                    analysis_parts.append(f"- 😴 **生活方式**：{len(recommendations['lifestyle'])}条")
                if recommendations.get("medical") and len(recommendations["medical"]) > 0:
                    analysis_parts.append(f"- 🏥 **就医建议**：{len(recommendations['medical'])}条")
                
                analysis_parts.append("\n您可以在上方的**个性化建议**栏目中查看具体的建议内容。")
            
            # 数据来源说明
            analysis_parts.append(f"\n---")
            analysis_parts.append(f"## 📋 重要声明")
            analysis_parts.append("> ⚠️ **以上分析基于您提供的健康咨询记录生成，仅供参考，不能替代专业医疗诊断。**\n"
                                "> 💊 **如有身体不适或健康疑虑，请及时咨询专业医生。**\n"
                                "> 🏥 **紧急情况请立即拨打120急救电话。**")
            
            return "\n".join(analysis_parts)
            
        except Exception as e:
            logger.error(f"生成综合分析失败: {str(e)}")
            return "基于您的健康数据，系统为您提供了个性化的健康评估和建议。请注意，这只是健康管理参考，不能替代专业医疗诊断。"

    def _get_default_analysis(self) -> Dict:
        """
        获取默认的分析结果
        
        Returns:
            默认分析结果
        """
        # 默认子项评分
        score_data = {
            "physical": 75,
            "mental": 75,  
            "lifestyle": 70  # 生活方式默认稍低
        }
        
        # 使用专门的工具方法计算平均值
        score_data["overall"] = self.calculate_average_score(score_data)
        
        return {
            "health_score": score_data,
            "risk_assessment": {
                "high_risk": [],
                "medium_risk": [],  # 没有足够数据时不编造风险，保持为空
                "low_risk": []
            },
            "trends": {},
            "recommendations": {
                "diet": [],      # 没有足够数据时不编造建议，保持为空
                "exercise": [],
                "lifestyle": [],
                "medical": []
            }
        }

# 创建全局健康分析服务实例
health_analysis_service = HealthAnalysisService()
