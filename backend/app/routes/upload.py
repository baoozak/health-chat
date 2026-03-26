"""
文件上传路由
处理文件上传并使用AI分析文件内容(支持TXT/Word/图片/PDF)
支持多轮对话上下文
"""
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
import os
import tempfile
import logging
import json

from app.database import get_mongodb
from app.services.ai_service import ai_service, AIService
from app.utils.auth import get_current_user
from app.utils.file_parser import FileParser
from app.dao.chat_dao import ChatDAO
from app.dao.session_dao import SessionDAO
from models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/upload", tags=["upload"])

@router.post("/file")
async def upload_file(
    file: UploadFile = File(...),
    message: str = Form(...),
    session_id: str = Form(...),
    current_user: User = Depends(get_current_user),
    mongodb: AsyncIOMotorDatabase = Depends(get_mongodb)
):
    """
    上传文件并进行AI对话（支持多轮对话上下文）
    支持: TXT, Word, JPG, PNG, PDF
    
    Args:
        file: 上传的文件
        message: 用户问题
        session_id: 会话ID
        current_user: 当前用户
        mongodb: MongoDB数据库
        
    Returns:
        流式AI回复
    """
    temp_file_path = None
    
    try:
        logger.info(f"收到文件上传: {file.filename}, 用户: {current_user.username}")
        
        # 1. 验证文件
        content = await file.read()
        file_size = len(content)
        
        is_valid, error_msg = FileParser.validate_file(file.filename, file_size)
        if not is_valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
        
        # 2. 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        logger.info(f"文件已保存到临时路径: {temp_file_path}")
        
        # 3. 保存用户消息(只保存用户问题，不保存文件名)
        user_message_content = message
        
        # 如果是图片文件，提取base64数据用于持久化存储
        image_data = None
        image_filename = None
        image_mime_type = None
        
        if FileParser.is_image_file(file.filename):
            import base64
            image_data = base64.b64encode(content).decode('utf-8')
            image_filename = file.filename
            image_mime_type = file.content_type or FileParser.get_mime_type(file.filename)
        
        await ChatDAO.save_message(
            mongodb, 
            current_user.id, 
            session_id, 
            "user", 
            user_message_content,
            image_data,
            image_filename,
            image_mime_type
        )
        
        # 4. 获取历史消息作为上下文
        history_messages = await ChatDAO.get_session_messages(
            db=mongodb,
            user_id=current_user.id,
            session_id=session_id
        )
        # 转换为LangChain格式（排除刚保存的当前消息）
        chat_history = AIService.convert_history_to_messages(
            history_messages[:-1] if history_messages else [],
            max_rounds=10
        )
        
        logger.info(f"加载了 {len(chat_history)} 条历史消息作为上下文")
        
        # 5. 使用AI处理(流式返回)
        async def generate_response():
            ai_response_parts = []
            pdf_temp_images = []
            
            try:
                # 根据文件类型选择处理方式
                if FileParser.is_image_file(file.filename):
                    # 处理图片文件
                    logger.info(f"处理图片文件: {file.filename}")
                    
                    # 使用视觉模型（带历史上下文）
                    async for chunk in ai_service.chat_stream_with_image(
                        message, temp_file_path, file.filename, chat_history
                    ):
                        ai_response_parts.append(chunk)
                        yield f"data: {json.dumps({'text': chunk}, ensure_ascii=False)}\n\n"
                
                elif FileParser.is_pdf_file(file.filename):
                    # 处理PDF文件
                    logger.info(f"处理PDF文件: {file.filename}")
                    # 转换为临时图片文件
                    pdf_temp_images = FileParser.pdf_to_temp_images(temp_file_path)
                    
                    # 分析第一页
                    if pdf_temp_images:
                        async for chunk in ai_service.chat_stream_with_image(
                            f"{message}\n\n(这是PDF的第1页)", 
                            pdf_temp_images[0], 
                            file.filename,
                            chat_history
                        ):
                            ai_response_parts.append(chunk)
                            yield f"data: {json.dumps({'text': chunk}, ensure_ascii=False)}\n\n"
                    else:
                        raise Exception("PDF文件为空或无法解析")
                
                else:
                    # 处理文本文件(TXT/Word)
                    logger.info(f"处理文本文件: {file.filename}")
                    file_content = FileParser.get_file_content(temp_file_path)

                    # 使用qwen-long模型处理文件（带历史上下文）
                    async for chunk in ai_service.chat_stream_with_file(
                        message, file_content, file.filename, chat_history
                    ):
                        ai_response_parts.append(chunk)
                        yield f"data: {json.dumps({'text': chunk}, ensure_ascii=False)}\n\n"
                
                # 完成标记
                yield "data: [DONE]\n\n"
                
                # 保存AI回复
                full_response = ''.join(ai_response_parts)
                await ChatDAO.save_message(
                    mongodb,
                    current_user.id,
                    session_id,
                    "ai",
                    full_response
                )
                
                # 更新会话
                await SessionDAO.update_session(
                    mongodb,
                    current_user.id,
                    session_id,
                    increment_message_count=True
                )
                
                logger.info("文件处理完成")
                
            except Exception as e:
                logger.error(f"AI处理失败: {str(e)}")
                error_msg = json.dumps({'error': str(e)}, ensure_ascii=False)
                yield f"data: {error_msg}\n\n"
            finally:
                # 清理上传的临时文件
                if temp_file_path and os.path.exists(temp_file_path):
                    try:
                        os.unlink(temp_file_path)
                        logger.info(f"已删除临时文件: {temp_file_path}")
                    except Exception as e:
                        logger.error(f"删除临时文件失败: {str(e)}")
                
                # 清理PDF生成的临时图片
                for img_path in pdf_temp_images:
                    if os.path.exists(img_path):
                        try:
                            os.unlink(img_path)
                            logger.info(f"已删除PDF临时图片: {img_path}")
                        except Exception as e:
                            logger.error(f"删除PDF临时图片失败: {str(e)}")
        
        return StreamingResponse(
            generate_response(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            }
        )
        
    except HTTPException:
        # 清理临时文件
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        raise
    except Exception as e:
        # 清理临时文件
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        logger.error(f"文件上传处理失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件处理失败: {str(e)}"
        )
