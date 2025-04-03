import streamlit as st
import pandas as pd
import re
import time
import random
import requests
from bs4 import BeautifulSoup

# Список user-agent для имитации разных браузеров
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/112.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.42'
]

def get_video_views(video_id):
    """Получает количество просмотров видео по его ID используя прямой парсинг страницы"""
    try:
        # Создаем URL из ID видео
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Случайная задержка от 2 до 5 секунд, чтобы избежать блокировки
        time.sleep(random.uniform(2, 5))
        
        # Выбираем случайный User-Agent
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Referer': 'https://www.google.com/'
        }
        
        # Делаем запрос
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Проверяем на ошибки HTTP
        
        # Парсим HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Извлекаем метаданные из JSON-скрипта
        scripts = soup.find_all('script')
        for script in scripts:
            script_text = script.string
            if script_text and 'var ytInitialData' in script_text:
                # Ищем число просмотров с помощью регулярного выражения
                view_count_match = re.search(r'"viewCount":\{"videoViewCountRenderer":\{"viewCount":\{"simpleText":"([\d,]+)', script_text)
                if view_count_match:
                    views_text = view_count_match.group(1)
                    # Удаляем запятые и преобразуем в число
                    return int(views_text.replace(',', ''))
        
        # Если не нашли в первом методе, пробуем другой паттерн
        for script in scripts:
            script_text = script.string
            if script_text and '"viewCount":' in script_text:
                view_count_match = re.search(r'"viewCount":"([\d,]+)"', script_text)
                if view_count_match:
                    views_text = view_count_match.group(1)
                    return int(views_text.replace(',', ''))
        
        return "Не удалось извлечь количество просмотров"
    except requests.HTTPError as e:
        return f"Ошибка HTTP: {str(e)}"
    except requests.RequestException as e:
        return f"Ошибка запроса: {str(e)}"
    except Exception as e:
        return f"Неожиданная ошибка: {str(e)}"

# Настройка страницы приложения
st.set_page_config(
    page_title="YouTube Views Parser",
    page_icon="📊",
    layout="wide",
)

# Заголовок приложения
st.title("Парсер просмотров YouTube видео")

# Инструкции для пользователя
st.markdown("""
Введите ID видео YouTube (по одному в каждой строке).
ID видео — это часть URL после `v=`. Например, для `https://www.youtube.com/watch?v=dQw4w9WgXcQ` ID будет `dQw4w9WgXcQ`.

**Рекомендация:** Вводите не более 5 ID видео за один запуск, чтобы избежать блокировки со стороны YouTube.
""")

# Поле ввода для ID видео
video_ids_input = st.text_area("Введите ID видео (по одному в строке):", height=200)

# Опция для полного URL
full_url_option = st.checkbox("Я ввожу полные URL видео (например, https://www.youtube.com/watch?v=dQw4w9WgXcQ)")

# Кнопка для запуска парсинга
if st.button("Получить просмотры"):
    if video_ids_input:
        # Разделяем введенный текст на строки и очищаем от пробелов
        lines = [line.strip() for line in video_ids_input.split("\n") if line.strip()]
        
        # Извлекаем ID видео из строк
        video_ids = []
        for line in lines:
            if full_url_option:
                # Пытаемся извлечь ID видео из полного URL
                match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', line)
                if match:
                    video_ids.append(match.group(1))
            else:
                # Предполагаем, что строка уже содержит только ID видео
                if re.match(r'^[0-9A-Za-z_-]{11}$', line):
                    video_ids.append(line)
        
        if not video_ids:
            st.error("Пожалуйста, введите корректные ID видео или URL YouTube.")
        else:
            # Создаем прогресс-бар
            progress_bar = st.progress(0)
            
            # Инициализируем список для хранения результатов
            results = []
            
            # Отображаем информацию о процессе
            status_text = st.empty()
            
            # Предупреждение о возможных ошибках
            st.warning("Обработка данных может занять некоторое время. Добавлены задержки между запросами для предотвращения блокировки.")
            
            # Добавляем счетчики успешных и неудачных запросов
            success_count = 0
            error_count = 0
            
            # Парсим данные для каждого ID
            for i, video_id in enumerate(video_ids):
                status_text.text(f"Обработка {i+1}/{len(video_ids)}: {video_id}")
                views = get_video_views(video_id)
                
                if isinstance(views, int):
                    success_count += 1
                    results.append({"ID видео": video_id, "Просмотры": views, "Статус": "Успешно"})
                else:
                    error_count += 1
                    results.append({"ID видео": video_id, "Просмотры": "N/A", "Статус": views})
                
                # Обновляем прогресс-бар
                progress_bar.progress((i + 1) / len(video_ids))
            
            # Создаем DataFrame из результатов
            df = pd.DataFrame(results)
            
            # Отображаем результаты в таблице
            st.subheader("Результаты:")
            st.dataframe(df)
            
            # Показываем статистику выполнения
            st.info(f"Обработано: {len(video_ids)} видео. Успешно: {success_count}. Ошибок: {error_count}.")
            
            # Создаем CSV-файл для скачивания
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Скачать данные как CSV",
                data=csv,
                file_name="youtube_views.csv",
                mime="text/csv",
            )
            
            status_text.text("Готово!")
    else:
        st.error("Пожалуйста, введите ID видео перед запуском.")

# Дополнительная информация
st.markdown("""
---
### Возможные проблемы и решения:

1. **Неудачное извлечение данных** - YouTube может блокировать автоматизированные запросы:
   - Пробуйте вводить не более 5 видео за один раз
   - Делайте паузы между запусками приложения
   - Помните, что YouTube активно защищается от скрейпинга данных

2. **Некорректные данные** - убедитесь, что вы вводите правильные ID видео:
   - Используйте опцию "Я ввожу полные URL" если вставляете целые ссылки
   - ID видео должны содержать 11 символов (например, `dQw4w9WgXcQ`)

*Примечание: Это приложение создано в образовательных целях. YouTube может запрещать автоматизированный сбор данных согласно их условиям использования.*
""") 