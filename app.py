import streamlit as st
import pandas as pd
import re
import time
import random
import requests
from bs4 import BeautifulSoup

# Включаем кэширование сессии для сохранения данных между перезагрузками
if 'results_df' not in st.session_state:
    st.session_state.results_df = None

if 'is_processing' not in st.session_state:
    st.session_state.is_processing = False

if 'last_input' not in st.session_state:
    st.session_state.last_input = ""

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
        # Проверяем валидность ID
        if not re.match(r'^[0-9A-Za-z_-]{11}$', video_id):
            return "Неверный формат ID видео"
            
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

# Функция для обработки ввода и получения ID видео
def process_input(input_text, is_full_url):
    lines = [line.strip() for line in input_text.split("\n")]
    processed_data = []
    
    for line in lines:
        if not line:  # Пропускаем пустые строки, но сохраняем их в результате
            processed_data.append({
                "Исходная строка": "",
                "ID видео": "",
                "Просмотры": "N/A",
                "Статус": "Пустая строка"
            })
            continue
            
        video_id = None
        if is_full_url:
            # Пытаемся извлечь ID видео из полного URL
            match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', line)
            if match:
                video_id = match.group(1)
        else:
            # Проверяем, соответствует ли строка формату ID видео
            if re.match(r'^[0-9A-Za-z_-]{11}$', line):
                video_id = line
        
        # Добавляем информацию о строке, независимо от того, удалось ли извлечь ID
        processed_data.append({
            "Исходная строка": line,
            "ID видео": video_id if video_id else "",
            "Просмотры": "N/A",
            "Статус": "Ожидает обработки" if video_id else "Неверный формат ID видео"
        })
    
    return processed_data

def main():
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
    
    **Рекомендация:** При большом количестве ID (более 100) процесс может занять много времени. 
    Вы можете отслеживать прогресс ниже.
    """)
    
    # Колонки для разделения интерфейса
    col1, col2 = st.columns([2, 3])
    
    with col1:
        # Поле ввода для ID видео
        video_ids_input = st.text_area(
            "Введите ID видео (по одному в строке):", 
            height=200,
            key="input_area",
            value=st.session_state.last_input
        )
        
        # Опция для полного URL
        full_url_option = st.checkbox("Я ввожу полные URL видео", key="full_url")
        
        # Кнопка для запуска парсинга
        start_button = st.button("Получить просмотры")
        
        if start_button and video_ids_input:
            # Сохраняем ввод пользователя
            st.session_state.last_input = video_ids_input
            # Обрабатываем ввод для получения ID видео
            processed_data = process_input(video_ids_input, full_url_option)
            
            # Создаем DataFrame для отслеживания прогресса
            df = pd.DataFrame(processed_data)
            st.session_state.results_df = df
            st.session_state.is_processing = True
            
            # Перезагружаем страницу для запуска обработки
            st.rerun()
    
    # Если есть данные и процесс запущен, начинаем обработку
    if st.session_state.is_processing and st.session_state.results_df is not None:
        df = st.session_state.results_df
        
        with col2:
            st.subheader("Ход выполнения:")
            
            # Создаем область для вывода прогресса
            progress_container = st.empty()
            progress_bar = st.progress(0)
            status_text = st.empty()
            count_text = st.empty()
            
            # Счетчики
            total_count = len(df)
            pending_count = sum(df["Статус"] == "Ожидает обработки")
            processed_count = total_count - pending_count
            success_count = sum(df["Статус"] == "Успешно")
            error_count = processed_count - success_count
            
            # Отображаем текущий прогресс
            progress_container.write(f"Обработано: {processed_count}/{total_count} строк")
            if total_count > 0:
                progress_bar.progress(processed_count / total_count)
            count_text.info(f"Успешно: {success_count}, Ошибок: {error_count}, Ожидает: {pending_count}")
            
            # Найти строки, которые еще не обработаны
            rows_to_process = df[df["Статус"] == "Ожидает обработки"].index.tolist()
            
            if rows_to_process:
                # Обрабатываем только одну строку за раз, чтобы обновлять интерфейс
                row_idx = rows_to_process[0]
                video_id = df.loc[row_idx, "ID видео"]
                
                if video_id:
                    status_text.write(f"Обработка: {video_id}")
                    views = get_video_views(video_id)
                    
                    if isinstance(views, int):
                        df.loc[row_idx, "Просмотры"] = views
                        df.loc[row_idx, "Статус"] = "Успешно"
                    else:
                        df.loc[row_idx, "Просмотры"] = "N/A"
                        df.loc[row_idx, "Статус"] = views
                
                # Обновляем DataFrame в session_state
                st.session_state.results_df = df
                
                # Обновляем страницу для продолжения обработки следующей строки
                time.sleep(0.1)  # Небольшая задержка перед обновлением
                st.rerun()
            else:
                # Все строки обработаны
                st.session_state.is_processing = False
                status_text.success("Обработка завершена!")
        
        # После завершения обработки или при наличии результатов, показываем их
        st.subheader("Результаты:")
        st.dataframe(df)
        
        # Предлагаем скачать результаты в CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Скачать данные как CSV",
            data=csv,
            file_name="youtube_views.csv",
            mime="text/csv",
        )
        
        # Кнопка для очистки результатов и перезапуска
        if st.button("Очистить результаты и начать заново"):
            st.session_state.results_df = None
            st.session_state.is_processing = False
            st.rerun()
    
    # Дополнительная информация
    st.markdown("""
    ---
    ### Возможные проблемы и решения:
    
    1. **Долгое время обработки** - при большом количестве ID:
       - Процесс может занять много времени из-за задержек между запросами
       - Вы можете оставить браузер открытым и вернуться позже
       - Результаты сохраняются даже после выгрузки CSV файла
    
    2. **Ошибки при извлечении данных** - YouTube может блокировать автоматизированные запросы:
       - При большом количестве запросов YouTube может временно блокировать ваш IP
       - Делайте паузы между запусками с большим количеством ID
    
    3. **Проблемы с форматом ввода**:
       - Убедитесь, что вы выбрали правильную опцию для формата ввода (ID или полный URL)
       - ID видео должны содержать 11 символов (например, `dQw4w9WgXcQ`)
    
    *Примечание: Это приложение создано в образовательных целях. YouTube может запрещать автоматизированный сбор данных согласно их условиям использования.*
    """)

if __name__ == "__main__":
    main() 