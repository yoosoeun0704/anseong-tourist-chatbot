import streamlit as st
import threading
from transformers import GPT2LMHeadModel, GPT2Tokenizer
from tornado import web, httpserver, ioloop

# Lock 객체 생성
lock = threading.Lock()

# 모델과 토크나이저 로드
model_name = "gpt2"
model = GPT2LMHeadModel.from_pretrained(model_name)
tokenizer = GPT2Tokenizer.from_pretrained(model_name)

# 관광 명소 정보
tourist_spots = {
    "팜랜드": {
        "description": "안성 팜랜드는 다양한 동물과 자연을 즐길 수 있는 테마파크입니다.",
        "image_url": "https://search.pstatic.net/common/?src=http%3A%2F%2Fblogfiles.naver.net%2FMjAyMzEwMTlfMTE4%2FMDAxNjk3NjQxMjg1NTM3.Fcjp-dKWWdrHRazvq9dfXJPcsN-JRnHN8coGpcsuJxog.FWfzF-789oEEQXTB9IPpvZ682J4IqfP2wjDuAbAfzeog.JPEG.otter86%2F1697641262847.jpg&type=sc960_832"
    },
    "남사당놀이마을": {
        "description": "안성 남사당놀이마을은 한국 전통 공연과 문화를 체험할 수 있는 곳입니다.",
        "image_url": "https://search.pstatic.net/common/?src=http%3A%2F%2Fblogfiles.naver.net%2F20140707_222%2Fhjne121_1404712263020yeWwV_PNG%2F11.png&type=sc960_832"
    },
    "안성맞춤랜드": {
        "description": "안성맞춤랜드는 가족과 함께 즐길 수 있는 놀이 시설과 자연 경관을 제공합니다.",
        "image_url": "https://search.pstatic.net/common/?src=http%3A%2F%2Fblogfiles.naver.net%2FMjAxNzA1MjJfMjEx%2FMDAxNDk1NDI1NDE3NDQx.0GN2nJlWyUjjQyiVNc2Ie7kUMHqMu7P1Sw69D5iSdzgg.Jpw9sLfl77Z-Mu8UkNzL8OvbxfVYPyS-64QnlNb7gwog.JPEG.wendellgee%2FDSC_5996.jpg&type=sc960_832"
    },
    "서운산": {
        "description": "서운산은 아름다운 경관과 등산로로 유명한 산입니다.",
        "image_url": "https://blog.naver.com/storyphoto/viewer.jsp?src=https%3A%2F%2Fimage.foresttrip.go.kr%2Ffrip%2F96c9c76b-1139-4403-a45e-c456f4b173fd.jpg"
    }
}

def generate_response(prompt, model, tokenizer, max_length=50):
    with lock:
        inputs = tokenizer.encode(prompt, return_tensors='pt')
        outputs = model.generate(inputs, max_length=max_length, num_return_sequences=1, no_repeat_ngram_size=2, pad_token_id=tokenizer.eos_token_id)
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response

def chatbot_response(user_input):
    with lock:
        if "안성의 관광명소를 추천해줘" in user_input:
            recommendations = list(tourist_spots.keys())[:3]
            return recommendations
        for spot in tourist_spots.keys():
            if spot in user_input:
                return [spot]
        return generate_response(user_input, model, tokenizer)

# Streamlit 애플리케이션을 실행하는 함수
def start_streamlit():
    # Streamlit UI
    st.title("T.OUR : 최선의 관광지를 추천해드립니다")
    user_input = st.text_input("안성의 관광명소에 대해 물어보세요!")
    if st.button("대답하기"):
        response = chatbot_response(user_input)
        if isinstance(response, list):
            for spot in response:
                info = tourist_spots.get(spot)
                if info:
                    st.image(info['image_url'], caption=spot)
                    st.write(f"**{spot}**: {info['description']}")
        else:
            st.write(response)

# Tornado 웹 서버를 실행하는 함수
def start_web_server():
    # Tornado 웹 애플리케이션 설정
    class MainHandler(web.RequestHandler):
        def get(self):
            self.write("T.OUR : 최선의 관광지를 추천해드립니다")
            user_input = self.get_argument("user_input", None)
            if user_input:
                response = chatbot_response(user_input)
                if isinstance(response, list):
                    for spot in response:
                        info = tourist_spots.get(spot)
                        if info:
                            self.write(f"<img src='{info['image_url']}' alt='{spot}'><br>")
                            self.write(f"<strong>{spot}</strong>: {info['description']}<br>")
                else:
                    self.write(response)

    app = web.Application([
        (r"/", MainHandler),
    ])

    http_server = httpserver.HTTPServer(app)
    http_server.listen(8502)  # 다른 포트 사용
    ioloop.IOLoop.current().start()

# 메인 함수
if __name__ == "__main__":
    # Streamlit 애플리케이션을 멀티 스레드로 실행
    streamlit_thread = threading.Thread(target=start_streamlit)
    streamlit_thread.start()

    # Tornado 웹 서버를 실행
    start_web_server()
