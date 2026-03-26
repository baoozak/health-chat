"""
AI对话服务
基于LangChain集成阿里百炼(ChatTongyi)实现AI对话功能
支持多轮对话记忆、流式输出、文件分析、图片分析
"""
import os
import base64
import logging
from typing import AsyncGenerator, List, Optional

from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    BaseMessage,
)
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from config.settings import settings

# 配置日志
logger = logging.getLogger(__name__)

# 确保环境变量中有API密钥（ChatTongyi会从环境变量读取）
os.environ["DASHSCOPE_API_KEY"] = settings.DASHSCOPE_API_KEY


class AIService:
    """
    AI对话服务类
    基于LangChain的ChatTongyi模型，支持多轮对话、流式输出、多模态分析
    """

    def __init__(self, system_prompt: str = None):
        """
        初始化AI服务
        
        Args:
            system_prompt: 系统提示词，用于设置AI的角色和规则
        """
        # 健康管理咨询系统专用提示词
        self.system_prompt = system_prompt or """你是一个专业的个人健康管理咨询助手。

【你的职责】
1. 分析用户描述的身体状况和健康数据
2. 提供科学的健康建议和生活方式指导
3. 解答健康、营养、运动相关疑问
4. 推荐健康的饮食和运动方案
5. 关注用户的整体身心健康

【重要原则 - 必须严格遵守】
⚠️ 你不是医生，不能做任何疾病诊断
⚠️ 不推荐具体药物品牌或剂量
⚠️ 遇到以下情况必须建议立即就医：
   - 急性疼痛、剧烈疼痛
   - 呼吸困难、胸痛
   - 严重出血、外伤
   - 意识障碍、昏迷
   - 高烧不退（超过39°C）
⚠️ 紧急情况提示：立即拨打120急救电话

【回答风格】
- 专业但通俗易懂，避免过多医学术语
- 基于科学证据和医学共识
- 关注用户整体健康，不是单一症状
- 给出具体、可操作的建议
- 保持温和、耐心、鼓励的态度

【健康建议覆盖范围】
✅ 健康生活方式（饮食、运动、睡眠）
✅ 常见健康问题的预防
✅ 体重管理和营养建议
✅ 压力管理和心理健康
✅ 慢性病的日常管理建议（配合医生治疗）

【不提供的服务】
❌ 疾病诊断
❌ 药物处方
❌ 替代专业医疗
❌ 手术或医疗程序建议

【免责声明 - 每次重要建议都要提醒】
本助手仅提供一般性健康信息和生活方式建议，不能替代专业医疗诊断和治疗。
如有身体不适或健康问题，请及时咨询专业医生。
"""

        # 从 .env 文件加载的 API 密钥
        api_key = settings.DASHSCOPE_API_KEY

        # 初始化对话模型（qwen-plus）
        self.llm = ChatTongyi(
            model="qwen-plus",
            dashscope_api_key=api_key,
            streaming=True,
        )

        # 初始化长文本模型（qwen-long，用于文件分析）
        self.long_llm = ChatTongyi(
            model="qwen-long",
            dashscope_api_key=api_key,
            streaming=True,
        )

        # 初始化视觉模型（qwen-vl-plus，用于图片分析）
        self.vision_llm = ChatTongyi(
            model="qwen-vl-plus",
            dashscope_api_key=api_key,
            streaming=True,
        )

        # 构建对话Prompt模板（包含历史消息占位符）
        self.chat_prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])

        # 构建对话Chain
        self.chain = self.chat_prompt | self.llm

        logger.info("AI服务初始化完成（LangChain + ChatTongyi）")
        logger.info(f"对话模型: qwen-plus, 长文本模型: qwen-long, 视觉模型: qwen-vl-plus")

    async def chat_stream(
        self,
        user_message: str,
        chat_history: Optional[List[BaseMessage]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        与AI进行异步流式对话（支持多轮上下文）

        Args:
            user_message: 用户消息
            chat_history: 历史消息列表（LangChain BaseMessage格式）

        Yields:
            AI回复的文本片段
        """
        try:
            logger.info(f"收到用户消息(流式): {user_message[:50]}...")

            # 使用 astream 异步流式调用，避免阻塞事件循环
            async for chunk in self.chain.astream({
                "input": user_message,
                "chat_history": chat_history or [],
            }):
                text = chunk.content
                if text:
                    yield text

            logger.info("流式AI回复完成")

        except Exception as e:
            logger.error(f"流式AI对话出错: {str(e)}")
            raise Exception(f"AI服务错误: {str(e)}")

    async def chat_stream_with_file(
        self,
        user_message: str,
        file_content: str,
        filename: str,
        chat_history: Optional[List[BaseMessage]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        带文件内容的异步流式对话，使用qwen-long模型

        Args:
            user_message: 用户问题
            file_content: 文件文本内容
            filename: 文件名
            chat_history: 历史消息列表

        Yields:
            AI回复的文本片段
        """
        try:
            logger.info(f"收到带文件的消息: 文件={filename}, 问题={user_message[:50]}...")

            # 健康报告分析的专用系统提示词
            file_system_prompt = """你是专业的健康报告分析助手。
            
【分析原则】
1. 仔细解读用户上传的健康报告、体检报告内容
2. 用通俗语言解释各项指标的含义
3. 指出异常指标并解释可能的原因
4. 提供改善建议（饮食、运动、生活方式）
5. 强调：报告解读不等于诊断，异常指标需咨询医生

【重要提醒】
⚠️ 如发现严重异常指标，务必建议用户尽快就医
⚠️ 不做疾病诊断，只做指标解读
⚠️ 不推荐药物治疗方案

【免责声明】
此分析仅供参考，不能替代专业医生的诊断。请携带报告咨询专业医生。
"""
            # 构造包含文件内容的消息
            context_message = f"""文件名: {filename}

文件内容:
{file_content}

---

用户问题: {user_message}

请基于上述文件内容进行健康分析和建议。"""

            # 构造消息列表
            messages = [
                SystemMessage(content=file_system_prompt),
                *(chat_history or []),
                HumanMessage(content=context_message),
            ]

            logger.info(f"使用qwen-long模型处理文件内容, 文件长度: {len(file_content)}")

            # 使用 astream 异步流式，避免阻塞事件循环
            async for chunk in self.long_llm.astream(messages):
                text = chunk.content
                if text:
                    yield text

            logger.info("文件处理AI回复完成")

        except Exception as e:
            logger.error(f"文件处理AI对话出错: {str(e)}")
            raise Exception(f"AI服务错误: {str(e)}")

    async def chat_stream_with_image(
        self,
        user_message: str,
        image_path: str,
        filename: str,
        chat_history: Optional[List[BaseMessage]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        带图片的异步流式对话，使用qwen-vl-plus视觉模型

        Args:
            user_message: 用户问题
            image_path: 图片本地路径
            filename: 文件名
            chat_history: 历史消息列表

        Yields:
            AI回复的文本片段
        """
        try:
            logger.info(f"收到图片分析请求: 文件={filename}, 路径={image_path}")

            # 视觉分析系统提示词
            vision_system_prompt = """你是专业的医疗图像分析助手。

【分析能力】
1. 识别体检报告、医疗图片中的文字和数据
2. 解读各项健康指标
3. 标注异常项并解释原因
4. 提供健康建议

【分析原则】
- 仔细观察图片中的所有信息
- 用通俗语言解释医学术语
- 指出需要关注的异常指标
- 提供饮食、运动等改善建议

【重要提醒】
⚠️ 这只是辅助分析，不是医疗诊断
⚠️ 发现严重异常请立即就医
⚠️ 不推荐具体药物

请详细分析用户上传的图片。"""

            # 读取图片并转为base64
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode("utf-8")

            # 检测图片MIME类型
            if filename.lower().endswith(".png"):
                image_type = "png"
            elif filename.lower().endswith((".jpg", ".jpeg")):
                image_type = "jpeg"
            else:
                image_type = "jpeg"

            logger.info(f"使用base64编码分析图片: {filename}, 类型: {image_type}")

            # 构造多模态消息（ChatTongyi视觉模型格式）
            messages = [
                SystemMessage(content=vision_system_prompt),
                HumanMessage(content=[
                    {"text": user_message},
                    {"image": f"data:image/{image_type};base64,{image_data}"},
                ]),
            ]

            logger.info(f"使用qwen-vl-plus模型分析图片: {filename}")

            # 使用 astream 异步流式，避免阻塞事件循环
            async for chunk in self.vision_llm.astream(messages):
                # 处理视觉模型的返回格式
                content = chunk.content
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and "text" in item:
                            yield item["text"]
                        elif isinstance(item, str):
                            yield item
                elif isinstance(content, str) and content:
                    yield content

            logger.info("图片分析完成")

        except Exception as e:
            logger.error(f"图片分析出错: {str(e)}")
            raise Exception(f"图片分析错误: {str(e)}")

    @staticmethod
    def convert_history_to_messages(
        history: List[dict],
        max_rounds: int = 10,
    ) -> List[BaseMessage]:
        """
        将MongoDB中的聊天记录转换为LangChain消息格式

        Args:
            history: MongoDB中的消息列表 [{"type": "user"/"ai", "content": "..."}]
            max_rounds: 最多保留的消息轮数

        Returns:
            LangChain BaseMessage列表
        """
        messages = []
        # 只取最近max_rounds条消息
        recent_history = history[-max_rounds * 2:] if history else []

        for msg in recent_history:
            content = msg.get("content", "")
            if not content:
                continue
            msg_type = msg.get("type", "")
            if msg_type == "user":
                messages.append(HumanMessage(content=content))
            elif msg_type == "ai":
                messages.append(AIMessage(content=content))

        return messages


# 创建全局AI服务实例
ai_service = AIService()
