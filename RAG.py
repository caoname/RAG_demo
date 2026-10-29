from langchain_core.documents import Document
import config_data as config
from langchain_ollama import OllamaEmbeddings
from vector_stores import VectorStoreService
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chat_models import init_chat_model
from langchain_core.runnables import RunnablePassthrough, RunnableWithMessageHistory, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from file_history_store import get_history
import os
from dotenv import load_dotenv
load_dotenv()


def print_prompt(prompt):
    print("="*20)
    print(prompt.to_string())
    print("="*20)
    return prompt


class RagService(object):

    def __init__(self):
        self.vector_service = VectorStoreService(
            embedding=OllamaEmbeddings(model=config.embedding_name)
        )

        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", "以我提供的已知参考资料为主，简洁专业的回答用户问题，参考资料：{context}"),
                ("system", "并且我提供的对话历史信息如下"),
                MessagesPlaceholder("chat_history"),
                ("user", "请回答用户提问：{input}")
            ]
        )

        self.chat_model = init_chat_model(
            model=config.chat_model,
            model_provider="openai",
            base_url="https://ws-a6ri4xf3p28cv81k.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
            api_key=os.getenv("qwen_API_KEY")
        )

        self.chain = self.__get_chain()

    """获取最终的执行链,__get_chain前面加下划线表示的是私有方法"""
    def __get_chain(self):
        # 获取上下文返回给retriever，但是此时格式不对需要转换
        retriever = self.vector_service.get_retriever()

        def format_document(docs: list[Document]):
            if not docs:
                return "无相关参考资料"

            formatted_docs = ""
            for doc in docs:
                formatted_docs += f"文档片段：{doc.page_content}\n元数据内容：{doc.metadata}\n"
            return formatted_docs

        # 检查报错的原因，先看看输入链之前的信息是什么结构
        # def temp1(data):
        #     print("=" * 20, data)
        #     return data
        # 打印信息发现{'input': '我的体重180斤，尺码推荐', 'chat_history': []}多了个'chat_history'，
        # 因为retriever要的只是input，多输入了一个就报错，所以认为改动一下，使得我们只取得input也就是str类型
        def format_for_retriever(data: dict) -> str:
            return data['input']
        """
        KeyError: "Input to ChatPromptTemplate is missing variables {'chat_history'}.  
        Expected: ['chat_history', 'context', 'input'] Received: ['input', 'context']
        改了之后发现"context": RunnableLambda(temp1) | retriever | format_document不报错了，但是
        输入到self.prompt_template提示词中是报错了，期望有chat—history但是没有，所以可以再加个函数取到
        chat-history再给self.prompt_template
        """
        # def temp2(data):
        #     print("=" * 20, data)
        #     return data
        # {'input': {'input': '我的体重180斤，尺码推荐', 'chat_history': []}, 'context': "文档片段：身高：155-165cm，
        # 发现其实是有chat_history，所以又需要认为的拼接一下才行

        # 认为拼接input，context，chat-history
        def format_for_prompt_template(data):
            # {input, context, chat_history}
            new_data = {}
            new_data["input"] = data["input"]["input"]
            new_data["context"] = data["context"]
            new_data["chat_history"] = data["input"]["chat_history"]
            return new_data

        chain = (
            {
                "input": RunnablePassthrough(),
                "context": RunnableLambda(format_for_retriever) | retriever | format_document
            } | RunnableLambda(format_for_prompt_template) | self.prompt_template | print_prompt | self.chat_model | StrOutputParser()
        )

        # 增强链
        conversation_chain = RunnableWithMessageHistory(
            chain,
            get_history,
            input_messages_key="input",
            history_messages_key="chat_history"
        )

        return conversation_chain


if __name__ == '__main__':
    session_config = {
        "configurable": {
            "session_id": "user_001",
        }
    }

    res = RagService().chain.invoke({"input": "羽绒服怎么保养？"}, session_config)
    print(res)
