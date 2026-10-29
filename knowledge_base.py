"""
检查md5数据是否存在向量库中，实现知识库
"""
import os
import config_data as config
import hashlib
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter     # 递归文本分割器
from datetime import datetime


def check_md5(md5_str: str):
    """检查传入的md5字符串是否已经被处理过了"""
    if not os.path.exists(config.md5_path):
        # if进入表示文件不存在，也就是这个md5没处理过，‘w’表示如果文件不存在会优先创建
        open(config.md5_path, 'w', encoding='utf-8').close()
        return False
    else:
        # 先读取文件，在readlines拿到里面全部的行的内容,再用for循环全部读取每一行进行处理
        for line in open(config.md5_path, 'r', encoding='utf-8').readlines():
            line = line.strip()         # 处理字符串前后的空格和回车，方便后续进行匹配
            if line == md5_str:
                return True             # 已处理过
        return False


def save_md5(md5_str: str):
    """将传入的md5字符串，记录到文件中保存"""
    with open(config.md5_path, 'a', encoding='utf-8') as f:
        f.write(md5_str + '\n')


def get_string_md5(input_str: str, encoding='utf-8'):
    """将传入的字符串转换为md5字符串"""
    # 将字符串转换为bytes字节数组，相当于还原成二进制
    # str_bytes是转换后的字节数组，也就是用utf-8还原成了二进制
    str_bytes = input_str.encode(encoding=encoding)

    # 创建md5对象
    md5_obj = hashlib.md5()     # 得到MD5对象
    md5_obj.update(str_bytes)   # 更新内容，传入即将要转换的字节数组
    md5_hex = md5_obj.hexdigest()   # 得到md5的十六进制字符串，方便阅读

    return md5_hex


# 知识库服务
class KnowledgeBaseService(object):
    def __init__(self):
        # 如果文件夹不存在就创建，存在就跳过
        os.makedirs(config.persist_directory, exist_ok=True)

        # 记录向量存储的实例，也就是chroma数据库
        self.chroma = Chroma(
            collection_name=config.collection_name,         # 数据库的表名
            embedding_function=OllamaEmbeddings(model="nomic-embed-text"),
            persist_directory=config.persist_directory      # 数据库存储文件夹
        )
        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size,               # 分割后文本段的最大长度
            chunk_overlap=config.chunk_overlap,         # 连续文本段之间的字符重叠数量
            separators=config.separators,               # 自然段落划分的符号
            length_function=len,                        # 使用python自带的len函数统计长度
        )         # 文本分割器的对象

    def upload_by_str(self, data: str, filename):
        """将传入的字符串向量化，存入向量数据库中"""
        # 先得到传入字符串的md5值
        md5_hex = get_string_md5(data)

        # 先判断这个md5值是否在知识库中，如果不在就进行分割，在就直接返回跳出upload_by_str方法
        if check_md5(md5_hex):
            return "[跳过]内容已存在知识库中"

        # 判断是否进行分割
        if len(data) > config.max_split_char_number:
            # 如果长度大于就直接吧data传进来进行字符串分割，分割成片段
            knowledge_chunk: list[str] = self.spliter.split_text(data)
        else:
            # 如果长度不够不分割也要保证类型统一，方便后续处理，这就体现了类型统一的重要性
            # 就直接把data传入成[data]，变成列表，只有data这一个元素
            knowledge_chunk = [data]

        metadata = {
            "source": filename,
            # 我们熟悉的格式是2026-02-02，但是datetime.now()获取的不是，所以需要点strftime
            "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            # 操作员，也就是谁上传的数据
            "operator": "CJ"
        }

        # 把内容都加载到向量库中
        self.chroma.add_texts(
            # iterable -> list/tuple （iterable迭代器，列表、元组都属于迭代器的一种）
            # 要求的是iterable套字符串也就是iterable[str]，刚好knowledge_chunk就是list[str]
            knowledge_chunk,
            # 第二个要传的是metadatas：list[dict]，但是当前没有，所以在这之前需要先定义一下元数据
            # 元数据就是指的数据来源，作者，时间等等，可以随便定义，只要在此处传入的格式一致就行，也就是list[dict]
            # 在外面组装好metadata直接传进来是不行的，因为现在的元数据是字典，类型不对，需要的是列表套字典
            # 现在需要给不同的数据赋予各自的元数据（但是都是同一个metadata，内容相同），也就是给knowledge_chunk每个知识片段赋予各自的元数据

            # 这个推导式的意思可以看成for chunk in knowledge_chunk，下划线_也是个变量，只是不需要它做任何事情，
            # 只是需要它来启动这个循环

            metadatas=[metadata for _ in knowledge_chunk]
        )
        """A for B in C，对于 C 里面的每一个元素 B，算一下 A。例如：
        nums = [10, 20, 30]
        result = [x * 2 for x in nums]
        # x=10→20, x=20→40, x=30→60  →  result = [20, 40, 60]
        回到代码：
        metadatas = [metadata for _ in chunks]
        对 chunks 里每个元素（名字懒得起，写成 _），把 metadata 丢进列表
        结果 = [metadata, metadata, metadata, ...]  数量 = len(chunks)
        """

        # 上面一开始做的是if check_md5(md5_hex):看这个md5值是否在知识库中，如果不在就进行下面的分割，
        # 等一系列处理操作，但是下面是我们自己对这个字符串进行的处理操作，操作之后肯定是要记录到md5txt文件，
        # 表明已经处理过了，下次就不再处理了
        save_md5(md5_hex)

        return "成功将内容载入向量库"


# if __name__ == '__main__':
#     service = KnowledgeBaseService()
#     r = service.upload_by_str("周杰伦", "testfile")
#     print(r)
