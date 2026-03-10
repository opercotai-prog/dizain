import streamlit as st
import google.generativeai as genai
import json
from PIL import Image
import os
import io

# --- НАСТРОЙКИ ---
GEMINI_KEY = os.environ.get('GEMINI_KEY') 
if not GEMINI_KEY:
    GEMINI_KEY = st.sidebar.text_input("Введите Gemini API Key", type="password")

if GEMINI_KEY:
    # Важно: Настройка API
    genai.configure(api_key=GEMINI_KEY)

# --- ИНТЕРФЕЙС ---
st.set_page_config(page_title="AI Дизайн 2.5", layout="wide")
st.title("🎨 Дизайн-сервис на Gemini 2.5 Flash")

col1, col2 = st.columns([1, 1])

with col1:
    uploaded_file = st.file_uploader("Загрузите фото", type=["jpg", "jpeg", "png"])
    user_text = st.text_area("Что изменить?", "Сделай современную спальню в синих тонах")
    submit_btn = st.button("🚀 Создать проект")

# --- ЛОГИКА ---
def get_design_analysis(image, text):
    # Используем v1beta для доступа к экспериментальным фишкам Nano Banana
    model = genai.GenerativeModel('models/gemini-2.5-flash')
    
    # Промпт изменен так, чтобы модель понимала: нужно ДВА разных блока в ответе
    prompt = f"""
    Ты — мультимодальный ИИ-дизайнер. 
    Твоя задача — выполнить два действия одновременно:
    
    1. Сгенерируй изображение нового интерьера на основе запроса: "{text}".
    2. Выдай текстовый блок в формате JSON со сметой. 
    
    JSON должен содержать:
    {{
      "analysis": "описание концепции",
      "total_cost": "сумма в рублях",
      "items": [{{"name": "предмет", "price": "цена"}}]
    }}
    
    Важно: Изображение должно быть фотореалистичным и учитывать архитектуру на фото, если оно приложено.
    """
    
    content = [prompt]
    if image:
        content.append(image)
        
    # Вызываем генерацию
    response = model.generate_content(content)
    
    res_data = {"json": None, "image": None}
    
    # ПРОВЕРКА ЧАСТЕЙ ОТВЕТА
    if response.candidates:
        for part in response.candidates[0].content.parts:
            # Если нашли текст (JSON)
            if part.text:
                try:
                    # Чистим текст от markdown-оберток
                    clean_json = part.text.replace('```json', '').replace('```', '').strip()
                    res_data["json"] = json.loads(clean_json)
                except:
                    st.error("Не удалось распарсить JSON. ИИ прислал: " + part.text[:100])
            
            # Если нашли картинку
            if part.inline_data:
                img_bytes = part.inline_data.data
                res_data["image"] = Image.open(io.BytesIO(img_bytes))
    
    return res_data

if submit_btn:
    if not GEMINI_KEY:
        st.error("Введите API Key!")
    else:
        with st.spinner('Gemini 2.5 Nano Banana работает...'):
            img_input = Image.open(uploaded_file) if uploaded_file else None
            
            result = get_design_analysis(img_input, user_text)
            
            with col2:
                # 1. Сначала показываем изображение
                if result["image"]:
                    st.subheader("Визуализация дизайна:")
                    st.image(result["image"], use_container_width=True)
                else:
                    st.error("⚠️ Модель 2.5 не вернула изображение. Это может быть связано с ограничениями региона или безопасности (Safety Filter).")
                    # Краткая отладка для тебя:
                    st.write("Типы данных в ответе:", [type(p) for p in result])

                # 2. Потом показываем данные
                if result["json"]:
                    data = result["json"]
                    st.success(f"### Смета: {data.get('total_cost')} ₽")
                    st.write(f"**Идея:** {data.get('analysis')}")
                    
                    st.write("### Список предметов:")
                    for item in data.get('items', []):
                        search_url = f"https://www.google.com/search?q=купить+{item['name'].replace(' ', '+')}"
                        st.markdown(f"- **[{item['name']}]({search_url})** — {item['price']} ₽")
