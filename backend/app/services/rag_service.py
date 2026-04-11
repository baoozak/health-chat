"""
RAG（检索增强生成）服务 —— 全局健康知识库
基于 LangChain + Chroma + DashScope Embeddings 实现

【设计定位】
  全局知识库：由管理员通过 build_knowledge_base.py 脚本预置健康文档
  所有用户对话时自动检索，用于增强 AI 回答的专业性和准确性

【核心流程】
  【建库阶段 - 运行 build_knowledge_base.py】
    健康文档（TXT/PDF/Word）
      → RecursiveCharacterTextSplitter 切分 chunk
      → DashScope text-embedding-v2 向量化
      → Chroma 本地持久化（backend/vector_stores/global/）

  【检索阶段 - 用户对话时自动触发】
    用户问题
      → DashScope text-embedding-v2 向量化
      → Chroma 相似度搜索（Top-K）
      → 返回最相关的健康知识片段
      → 拼入 Prompt 供 AI 参考作答
"""
import os
import logging
from typing import List, Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import DashScopeEmbeddings

from config.settings import settings

logger = logging.getLogger(__name__)

# 全局知识库的固定标识（所有用户共享）
GLOBAL_STORE_ID = "global"

# Chroma collection 名称
CHROMA_COLLECTION_NAME = "health_knowledge"


class RAGService:
    """
    RAG 服务类 —— 全局健康知识库管理

    知识库存储路径：backend/vector_stores/global/
    通过 build_knowledge_base.py 脚本预置健康文档
    """

    def __init__(self):
        # 内存缓存：避免重复从磁盘加载
        self._store: Optional[Chroma] = None

        # 文本分割器（对中文分段友好）
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.RAG_CHUNK_SIZE,
            chunk_overlap=settings.RAG_CHUNK_OVERLAP,
            separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""],
        )

        # DashScope Embeddings（与 LLM 共用同一 API Key）
        self._embeddings = DashScopeEmbeddings(
            model="text-embedding-v2",
            dashscope_api_key=settings.DASHSCOPE_API_KEY,
        )

        # 确保向量库根目录存在
        os.makedirs(settings.rag_vector_store_path, exist_ok=True)
        logger.info(
            f"RAG 服务初始化完成，全局知识库路径: {self._get_store_path()}"
        )

    def _get_store_path(self) -> str:
        """获取全局知识库在磁盘上的路径"""
        return os.path.join(settings.rag_vector_store_path, GLOBAL_STORE_ID)

    def _load_store(self) -> Optional[Chroma]:
        """
        加载全局 Chroma 向量库（内存缓存优先）

        Returns:
            Chroma 实例，知识库不存在时返回 None
        """
        if self._store is not None:
            return self._store

        store_path = self._get_store_path()
        if os.path.exists(store_path):
            try:
                self._store = Chroma(
                    collection_name=CHROMA_COLLECTION_NAME,
                    embedding_function=self._embeddings,
                    persist_directory=store_path,
                )
                # 检查 collection 中是否有文档
                if self._store._collection.count() == 0:
                    logger.debug("Chroma collection 为空，视为未建库")
                    self._store = None
                    return None
                logger.info(f"全局知识库已从磁盘加载: {store_path}")
                return self._store
            except Exception as e:
                logger.error(f"加载全局知识库失败: {e}")
                return None

        logger.debug("全局知识库尚未建立，请运行 build_knowledge_base.py")
        return None

    def _create_store(self, documents: List[Document]) -> Chroma:
        """
        根据文档列表创建新的 Chroma 向量库并持久化到磁盘

        Args:
            documents: 待索引的文档列表

        Returns:
            新创建的 Chroma 实例
        """
        store_path = self._get_store_path()
        os.makedirs(store_path, exist_ok=True)

        store = Chroma.from_documents(
            documents=documents,
            embedding=self._embeddings,
            collection_name=CHROMA_COLLECTION_NAME,
            persist_directory=store_path,
        )
        self._store = store
        logger.info(f"全局知识库已创建并保存: {store_path}")
        return store

    async def add_documents(
        self,
        texts: List[str],
        filenames: List[str],
    ) -> int:
        """
        将文档批量向量化并存入全局知识库（供 build_knowledge_base.py 调用）

        支持增量追加：多次调用会合并到同一向量库，不会覆盖已有知识

        Args:
            texts: 文档文本列表
            filenames: 对应的文件名列表（作为元数据）

        Returns:
            成功索引的 chunk 总数，失败时返回 0
        """
        if not texts:
            return 0

        try:
            all_documents = []
            for text, filename in zip(texts, filenames):
                if not text or not text.strip():
                    logger.warning(f"文档内容为空，跳过: {filename}")
                    continue

                chunks = self._splitter.split_text(text)
                documents = [
                    Document(
                        page_content=chunk,
                        metadata={
                            "filename": filename,
                            "chunk_index": i,
                            "source": "global_knowledge_base",
                        },
                    )
                    for i, chunk in enumerate(chunks)
                ]
                all_documents.extend(documents)
                logger.info(f"文档切分: {filename} → {len(chunks)} 个 chunk")

            if not all_documents:
                return 0

            # 向量化 + 存入 Chroma
            existing_store = self._load_store()
            if existing_store is None:
                # 首次建库
                self._create_store(all_documents)
                logger.info("创建新的全局知识库")
            else:
                # 增量追加：直接向现有 collection 添加文档
                existing_store.add_documents(all_documents)
                logger.info("增量追加到现有全局知识库")

            logger.info(f"全局知识库更新完成，本次新增 {len(all_documents)} 个 chunk")
            return len(all_documents)

        except Exception as e:
            logger.error(f"知识库建立失败: {e}", exc_info=True)
            return 0

    async def retrieve(self, query: str, top_k: int = None) -> List[str]:
        """
        从全局知识库检索与问题最相关的健康知识片段

        Args:
            query: 用户的问题文本
            top_k: 返回数量，默认使用配置中的 RAG_TOP_K

        Returns:
            相关知识片段列表（已去重），知识库不存在时返回空列表
        """
        if top_k is None:
            top_k = settings.RAG_TOP_K

        store = self._load_store()
        if store is None:
            return []  # 无知识库时静默降级，不影响对话流程

        try:
            docs = await store.asimilarity_search(query, k=top_k)

            # 去重
            seen = set()
            results = []
            for doc in docs:
                content = doc.page_content.strip()
                if content and content not in seen:
                    seen.add(content)
                    results.append(content)

            if results:
                logger.info(
                    f"RAG 检索完成: 找到 {len(results)} 个相关知识片段 "
                    f"(query='{query[:30]}...')"
                )
            return results

        except Exception as e:
            logger.error(f"RAG 检索失败（降级为空）: {e}")
            return []

    def has_knowledge_base(self) -> bool:
        """
        检查全局知识库是否已建立

        Returns:
            True 表示知识库已存在，False 表示尚未建立
        """
        if self._store is not None:
            return True
        store_path = self._get_store_path()
        return os.path.exists(store_path)

    def build_rag_context(self, retrieved_chunks: List[str]) -> str:
        """
        将检索到的知识片段格式化为可注入 Prompt 的参考资料字符串

        Args:
            retrieved_chunks: retrieve() 返回的文本片段列表

        Returns:
            格式化后的参考资料字符串（为空时返回空字符串）
        """
        if not retrieved_chunks:
            return ""

        parts = ["【健康知识库参考资料】"]
        for i, chunk in enumerate(retrieved_chunks, 1):
            parts.append(f"\n[知识片段 {i}]\n{chunk}")
        parts.append("\n【请结合以上专业知识回答用户问题，如知识库内容与问题无关可忽略】\n")
        return "\n".join(parts)


# ─── 全局单例 ─────────────────────────────────────────────────────────────────
rag_service = RAGService()
