import gradio as gr
from chatbot import ask_chatgpt

def chat_interface(message):
    return ask_chatgpt(message)

gr.Interface(
    fn=chat_interface,
    inputs=gr.Textbox(lines=2, placeholder="무엇이든 물어보세요! 예) 이번주 상추 시세 알려줘"),
    outputs="text",
    title="농산물 시세 챗봇 (크롤링 기반)",
    description="kamis.or.kr 사이트에서 실시간 농산물 시세를 크롤링하여 알려줍니다."
).launch()
