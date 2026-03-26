"""
全局健康知识库构建脚本
在 backend/ 目录下运行：python build_knowledge_base.py

功能：
  将 knowledge_docs/ 目录下的所有 TXT 文件批量向量化，
  写入 FAISS 全局知识库（vector_stores/global/）。

  知识库建立后，所有用户的对话都会自动检索这些健康知识，
  AI 回答将基于真实的专业文档内容，而非纯粹依赖模型训练知识。

支持格式：.txt（当前）
可扩展：.docx / .pdf（按需添加解析器）

使用方式：
  cd backend
  python build_knowledge_base.py            # 增量追加（推荐）
  python build_knowledge_base.py --rebuild  # 清空重建
"""
import asyncio
import os
import sys
import argparse
import shutil
import logging

# 确保 backend/ 目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# 知识文档目录（相对于 backend/）
KNOWLEDGE_DOCS_DIR = os.path.join(os.path.dirname(__file__), "knowledge_docs")


def parse_args():
    parser = argparse.ArgumentParser(description="构建健康知识库")
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="清空现有知识库后重新构建（默认为增量追加）",
    )
    parser.add_argument(
        "--docs-dir",
        default=KNOWLEDGE_DOCS_DIR,
        help=f"知识文档目录（默认：{KNOWLEDGE_DOCS_DIR}）",
    )
    return parser.parse_args()


def read_txt_file(filepath: str) -> str:
    """读取 TXT 文件，自动处理 UTF-8 / GBK 编码"""
    for encoding in ("utf-8", "gbk", "utf-8-sig"):
        try:
            with open(filepath, "r", encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise ValueError(f"无法识别文件编码: {filepath}")


async def build(docs_dir: str, rebuild: bool):
    from config.settings import settings
    from app.services.rag_service import rag_service

    print("\n" + "=" * 55)
    print("  全局健康知识库构建工具")
    print("=" * 55)

    # 检查文档目录
    if not os.path.exists(docs_dir):
        logger.error(f"知识文档目录不存在: {docs_dir}")
        logger.info("请在 backend/knowledge_docs/ 目录下放置 .txt 健康文档")
        sys.exit(1)

    # --rebuild：清空现有知识库
    if rebuild:
        store_path = rag_service._get_store_path()
        if os.path.exists(store_path):
            shutil.rmtree(store_path)
            rag_service._store = None
            logger.info(f"已清空现有知识库: {store_path}")
        else:
            logger.info("知识库不存在，直接新建")

    # 扫描文档目录
    txt_files = [
        f for f in os.listdir(docs_dir)
        if f.endswith(".txt") and not f.startswith(".")
    ]

    if not txt_files:
        logger.warning(f"未找到任何 .txt 文件，请将健康文档放入: {docs_dir}")
        sys.exit(0)

    print(f"\n发现 {len(txt_files)} 个文档待处理：")
    for f in txt_files:
        path = os.path.join(docs_dir, f)
        size_kb = os.path.getsize(path) / 1024
        print(f"  ✦ {f} ({size_kb:.1f} KB)")

    print("\n开始向量化（调用 DashScope text-embedding-v2）...")
    print("该过程需要调用 API，请确保网络连接正常\n")

    # 读取所有文档
    texts, filenames = [], []
    for filename in txt_files:
        filepath = os.path.join(docs_dir, filename)
        try:
            text = read_txt_file(filepath)
            texts.append(text)
            filenames.append(filename)
            logger.info(f"读取成功: {filename} ({len(text)} 字符)")
        except Exception as e:
            logger.error(f"读取失败: {filename} — {e}")

    if not texts:
        logger.error("所有文档读取失败，退出")
        sys.exit(1)

    # 批量构建知识库
    total_chunks = await rag_service.add_documents(texts, filenames)

    # 输出结果
    print("\n" + "=" * 55)
    if total_chunks > 0:
        store_path = rag_service._get_store_path()
        print(f"  ✅ 知识库构建成功！")
        print(f"  📄 处理文档数：{len(texts)}")
        print(f"  🧩 生成 chunk 数：{total_chunks}")
        print(f"  💾 存储路径：{store_path}")
        print(f"\n  现在启动后端服务，AI 对话将自动检索这些健康知识。")
    else:
        print("  ❌ 知识库构建失败，请检查 API Key 和网络连接")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(build(args.docs_dir, args.rebuild))
