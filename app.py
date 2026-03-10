import streamlit as st
import google.generativeai as genai
import json
import requests
from PIL import Image
import os

# --- НАСТРОЙКИ ---
# API Ключ берем из секретов или вводим вручную
GEMINI_KEY = os.environ.get('GEMINI_KEY') 
if not GEMINI_KEY:
    GEMINI_KEY = st.sidebar.text_input("Введите Gemini API Key", type="password")

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

# --- ИНТЕРФЕЙС ---
st.set_page_config(page_title="AI Дизайн Интерьера", layout="wide")
st.title("🎨 Дизайн и расчет стоимости ремонта")
st.write("Загрузите фото комнаты и напишите пожелания — ИИ создаст новый дизайн и посчитает смету.")

col1, col2 = st.columns([1, 1])

with col1:
    uploaded_file = st.file_uploader("Загрузите фото (необязательно)", type=["jpg", "jpeg", "png"])
    user_text = st.text_area("Что вы хотите изменить?", placeholder="Например: Сделай кухню в стиле лофт, бюджет 200к")
    submit_btn = st.button("Рассчитать и создать дизайн")

# --- ЛОГИКА ---
def get_design_analysis(image, text):
    model = genai.GenerativeModel('models/gemini-2.5-flash:generateContent')
    
    prompt = f"""
    Ты эксперт по дизайну интерьера. Проанализируй запрос: "{text}".
    Если есть фото, используй его как основу.
    
    Выдай ответ СТРОГО в формате JSON (без лишних слов):
    {{
      "analysis": "краткое описание решения",
      "total_cost": "общая сумма в рублях",
      "items": [
        {{"name": "название предмета", "price": "цена"}}
      ],
      "image_prompt": "detailed professional interior design photo prompt in english for {text}, highly detailed, 8k, photorealistic"
    }}
    """
    
    content = [prompt]
    if image:
        content.append(image)
        
    response = model.generate_content(content)
    # Очистка JSON
    json_str = response.text.replace('```json', '').replace('```', '').strip()
    return json.loads(json_str)

if submit_btn:
    if not GEMINI_KEY:
        st.error("Нужен API Ключ Gemini!")
    else:
        with st.spinner('Магия ИИ в процессе...'):
            img = Image.open(uploaded_file) if uploaded_file else None
            
            # 1. Получаем анализ от Gemini
            data = get_design_analysis(img, user_text)
            
            with col2:
                st.subheader("Результат:")
                st.write(f"**Идея:** {data['analysis']}")
                st.write(f"### 💰 Ориентировочная стоимость: {data['total_cost']} руб.")
                
                # 2. Генерируем фото дизайна (используем бесплатный Pollinations.ai)
                # Это создаст картинку на лету по промпту от Gemini
                gen_image_url = f"https://pollinations.ai/p/{data['image_prompt'].replace(' ', '_')}?width=800&height=600&seed=42"
                st.image(gen_image_url, caption="Сгенерированный вариант дизайна")
                
                # 3. Список покупок
                st.write("### 🛒 Где купить предметы:")
                for item in data['items']:
                    search_url = f"https://www.google.com/search?q=купить+{item['name'].replace(' ', '+')}"
                    st.markdown(f"- **{item['name']}** (~{item['price']}р) — [Найти в магазинах]({search_url})")

# --- ИНСТРУКЦИЯ ---
with st.expander("Как запустить?"):
    st.write("""
    1. Установите библиотеку: `pip install streamlit google-generativeai Pillow requests`
    2. Запустите: `streamlit run app.py`
    3. Получите бесплатный ключ Gemini в Google AI Studio.
    """)
