
md5_path = "./md5.txt"

collection_name = "rag"
persist_directory = "./chroma"

chunk_size = 1000           # 每个分段允许的最大长度
chunk_overlap = 100         # 两个自然分段之间的重叠字符允许为100
# 分割字符
separators = ["\n\n", "\n", ".", "!", "?", "。", "！", "？", "。", " ", ""]  # 最后是空字符串
max_split_char_number = 1000    # 文本分割的阈值，超过这个长度才分割

similarity_threshold = 1   # 检索返回匹配的文档数量

embedding_name = "nomic-embed-text"
chat_model = "qwen3.8-flash"

session_config = {
    "configurable": {
        "session_id": "user_001",
    }
}
