import streamlit as st
import google.generativeai as genai
import json
import os
from PIL import Image
import io

# --- НАСТРОЙКИ ---
st.set_page_config(page_title="Gemini 2.0 Design Studio", layout="wide")

# Подключаем API Ключ
GEMINI_KEY = st.secrets.get("GEMINI_KEY") or os.environ.get("GEMINI_KEY")

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
else:
    st.error("Добавьте GEMINI_KEY в Secrets!")
    st.stop()

# --- ФУНКЦИЯ ОБРАБОТКИ ---
def generate_design_all_in_one(user_img, user_query):
    # Используем флагманскую мультимодальную модель 2.0
    model = genai.GenerativeModel("gemini-2.0-flash")
    
    prompt = f"""
    Ты — профессиональный ИИ-дизайнер. 
    1. Проанализируй приложенное фото и запрос пользователя: "{user_query}".
    2. Создай новый дизайн интерьера.
    3. В ответе выдай ДВЕ ВЕЩИ:
       - Текстовый блок в формате JSON со сметой и описанием.
       - Сгенерируй реалистичное изображение (фото) этого нового дизайна.
    
    JSON format:
    {{
      "concept": "краткое описание",
      "total_price": "сумма в рублях",
      "shopping_list": [
        {{"item": "название", "price": "цена"}}
      ]
    }}
    """
    
    # Собираем запрос (текст + фото пользователя, если есть)
    request_content = [prompt]
    if user_img:
        request_content.append(user_img)
    
    try:
        # Мощный мультимодальный запрос
        response = model.generate_content(request_content)
        
        res_data = {
            "json": None,
            "image": None
        }

        # Разбираем мультимодальный ответ
        for part in response.candidates[0].content.parts:
            # Если часть ответа - это текст (наш JSON)
            if part.text:
                import re
                json_match = re.search(r'\{.*\}', part.text, re.DOTALL)
                if json_match:
                    res_data["json"] = json.loads(json_match.group())
            
            # Если часть ответа - это изображение (inline_data)
            if part.inline_data:
                img_bytes = part.inline_data.data
                res_data["image"] = Image.open(io.BytesIO(img_bytes))
                
        return res_data
    except Exception as e:
        st.error(f"Ошибка модели 2.0: {e}")
        return None

# --- ИНТЕРФЕЙС ---
st.title("⚡ Gemini 2.0 Native Design Service")
st.write("Генерация интерьера и расчет сметы одной нейросетью")

col1, col2 = st.columns([1, 1.2])

with col1:
    uploaded_file = st.file_uploader("Загрузите фото комнаты", type=["jpg", "png"])
    user_text = st.text_area("Что вы хотите изменить?", "Сделай современную ванную в стиле спа")
    submit = st.button("🚀 Создать проект")

if submit:
    with st.spinner("Gemini 2.0 генерирует текст и изображение..."):
        input_img = Image.open(uploaded_file) if uploaded_file else None
        result = generate_design_all_in_one(input_img, user_text)
        
        if result:
            with col2:
                # Показываем СГЕНЕРИРОВАННОЕ изображение
                if result["image"]:
                    st.subheader("🖼 Визуализация от Gemini 2.0")
                    st.image(result["image"], use_container_width=True)
                else:
                    st.warning("Изображение не было сгенерировано. Попробуйте еще раз.")
                
                # Показываем JSON данные
                if result["json"]:
                    data = result["json"]
                    st.success(f"### Общая смета: {data.get('total_price')} ₽")
                    st.write(f"**Концепция:** {data.get('concept')}")
                    
                    st.write("### Список предметов:")
                    for item in data.get('shopping_list', []):
                        search_url = f"https://www.google.com/search?q=купить+{item['item'].replace(' ', '+')}"
                        st.markdown(f"- **[{item['item']}]({search_url})** — {item['price']} ₽")
