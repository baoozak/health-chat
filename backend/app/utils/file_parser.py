"""
文件解析工具
支持TXT、Word、图片、PDF等文件格式的内容提取
"""
import os
import io
import base64
import logging
from typing import Optional, Tuple, List
from docx import Document
from PIL import Image
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

class FileParser:
    """文件解析器"""
    
    # 支持的文件格式
    SUPPORTED_TEXT_FORMATS = ['.txt', '.docx']
    SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png']
    SUPPORTED_PDF_FORMATS = ['.pdf']
    
    # 最大文件大小
    MAX_TEXT_FILE_SIZE = 10 * 1024 * 1024  # 10MB for text files
    MAX_IMAGE_FILE_SIZE = 20 * 1024 * 1024  # 20MB for images/PDF
    
    @staticmethod
    def parse_txt(file_path: str, encoding: str = 'utf-8') -> str:
        """
        解析TXT文件
        
        Args:
            file_path: 文件路径
            encoding: 文件编码，默认UTF-8
            
        Returns:
            文件文本内容
        """
        try:
            # 尝试UTF-8编码
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            logger.info(f"成功解析TXT文件: {file_path}, 长度: {len(content)}")
            return content
        except UnicodeDecodeError:
            # 如果UTF-8失败，尝试GBK编码
            logger.warning(f"UTF-8解码失败，尝试GBK编码: {file_path}")
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    content = f.read()
                logger.info(f"使用GBK成功解析TXT文件: {file_path}")
                return content
            except Exception as e:
                logger.error(f"GBK解码也失败: {str(e)}")
                raise Exception("无法识别文件编码，请确保文件为UTF-8或GBK编码")
        except Exception as e:
            logger.error(f"解析TXT文件失败: {str(e)}")
            raise Exception(f"解析TXT文件失败: {str(e)}")
    
    @staticmethod
    def parse_docx(file_path: str) -> str:
        """
        解析Word文档(.docx)
        
        Args:
            file_path: 文件路径
            
        Returns:
            文档文本内容
        """
        try:
            doc = Document(file_path)
            
            # 提取所有段落文本
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            content = '\n'.join(paragraphs)
            
            logger.info(f"成功解析Word文件: {file_path}, 段落数: {len(paragraphs)}, 长度: {len(content)}")
            return content
        except Exception as e:
            logger.error(f"解析Word文件失败: {str(e)}")
            raise Exception(f"解析Word文件失败: {str(e)}")
    
    @staticmethod
    def image_to_base64(file_path: str) -> str:
        """
        将图片转换为base64编码
        
        Args:
            file_path: 图片文件路径
            
        Returns:
            base64编码的图片字符串
        """
        try:
            with Image.open(file_path) as img:
                # 压缩大图片以节省API调用成本
                max_size = (1024, 1024)
                if img.width > max_size[0] or img.height > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    logger.info(f"图片已压缩: {file_path}, 新尺寸: {img.size}")
                
                # 转换为RGB模式（确保兼容性）
                if img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')
                
                # 保存到内存并编码
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85)
                base64_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                logger.info(f"成功将图片转为base64: {file_path}, 编码长度: {len(base64_str)}")
                return base64_str
        except Exception as e:
            logger.error(f"图片转base64失败: {str(e)}")
            raise Exception(f"图片处理失败: {str(e)}")
    
    @staticmethod
    def pdf_to_temp_images(file_path: str) -> List[str]:
        """
        将PDF转换为临时图片文件列表
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            临时图片文件路径列表
        """
        import tempfile
        
        try:
            image_paths = []
            pdf_document = fitz.open(file_path)
            
            logger.info(f"PDF页数: {len(pdf_document)}")
            
            # 限制最多处理前5页
            max_pages = min(5, len(pdf_document))
            
            for page_num in range(max_pages):
                page = pdf_document[page_num]
                # 渲染页面为图片
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                
                # 创建临时文件
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                pix.save(temp_file.name)
                temp_file.close()
                
                image_paths.append(temp_file.name)
                logger.info(f"PDF第{page_num + 1}页已保存为: {temp_file.name}")
            
            pdf_document.close()
            return image_paths
        except Exception as e:
            logger.error(f"PDF转图片失败: {str(e)}")
            # 清理已创建的文件
            for path in image_paths:
                if os.path.exists(path):
                    os.unlink(path)
            raise Exception(f"PDF处理失败: {str(e)}")

    @staticmethod
    def pdf_to_images(file_path: str) -> List[str]:
        """
        将PDF转换为图片列表（base64编码）
        (保留此方法用于兼容性，但建议使用pdf_to_temp_images)
        """
        try:
            images = []
            pdf_document = fitz.open(file_path)
            
            # ... (保留原有逻辑)
            max_pages = min(5, len(pdf_document))
            
            for page_num in range(max_pages):
                page = pdf_document[page_num]
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img_data = pix.tobytes("jpeg")
                base64_str = base64.b64encode(img_data).decode('utf-8')
                images.append(base64_str)
            
            pdf_document.close()
            return images
        except Exception as e:
            logger.error(f"PDF转图片失败: {str(e)}")
            raise Exception(f"PDF处理失败: {str(e)}")
    
    @staticmethod
    def is_text_file(filename: str) -> bool:
        """判断是否为文本文件"""
        ext = os.path.splitext(filename)[1].lower()
        return ext in FileParser.SUPPORTED_TEXT_FORMATS
    
    @staticmethod
    def is_image_file(filename: str) -> bool:
        """判断是否为图片文件"""
        ext = os.path.splitext(filename)[1].lower()
        return ext in FileParser.SUPPORTED_IMAGE_FORMATS
    
    @staticmethod
    def get_mime_type(filename: str) -> str:
        """根据文件扩展名获取MIME类型"""
        ext = os.path.splitext(filename)[1].lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.txt': 'text/plain',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.pdf': 'application/pdf'
        }
        return mime_types.get(ext, 'application/octet-stream')
    
    @staticmethod
    def is_pdf_file(filename: str) -> bool:
        """判断是否为PDF文件"""
        ext = os.path.splitext(filename)[1].lower()
        return ext in FileParser.SUPPORTED_PDF_FORMATS
    
    @staticmethod
    def get_file_content(file_path: str) -> str:
        """
        统一的文件内容获取入口（仅用于文本文件）
        自动识别文件格式并调用对应解析器
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件文本内容
            
        Raises:
            Exception: 文件格式不支持或解析失败
        """
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise Exception(f"文件不存在: {file_path}")
        
        # 获取文件扩展名
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        # 检查格式是否支持
        if ext not in FileParser.SUPPORTED_TEXT_FORMATS:
            raise Exception(f"不支持的文本文件格式: {ext}")
        
        # 根据格式调用对应解析器
        if ext == '.txt':
            return FileParser.parse_txt(file_path)
        elif ext == '.docx':
            return FileParser.parse_docx(file_path)
        else:
            raise Exception(f"未实现的文件格式解析: {ext}")
    
    @staticmethod
    def validate_file(filename: str, file_size: int) -> Tuple[bool, Optional[str]]:
        """
        验证文件
        
        Args:
            filename: 文件名
            file_size: 文件大小(字节)
            
        Returns:
            (是否有效, 错误信息)
        """
        # 检查文件扩展名
        _, ext = os.path.splitext(filename)
        ext = ext.lower()
        
        # 支持的所有格式
        all_formats = (FileParser.SUPPORTED_TEXT_FORMATS + 
                      FileParser.SUPPORTED_IMAGE_FORMATS + 
                      FileParser.SUPPORTED_PDF_FORMATS)
        
        if ext not in all_formats:
            return False, f"不支持的文件格式: {ext}，支持: TXT, Word, JPG, PNG, PDF"
        
        # 检查文件大小（图片和PDF允许更大）
        if ext in FileParser.SUPPORTED_TEXT_FORMATS:
            max_size = FileParser.MAX_TEXT_FILE_SIZE
            if file_size > max_size:
                return False, f"文本文件过大: {file_size / 1024 / 1024:.2f}MB，最大支持10MB"
        else:
            max_size = FileParser.MAX_IMAGE_FILE_SIZE
            if file_size > max_size:
                return False, f"图片/PDF文件过大: {file_size / 1024 / 1024:.2f}MB，最大支持20MB"
        
        return True, None
