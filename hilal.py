from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import speech_recognition as sr
import pyttsx3
import json
import requests
from datetime import datetime
from difflib import get_close_matches
import os
from bs4 import BeautifulSoup
import random
import re

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Oturum için gizli anahtar
def veritabanı_dosya_yolu():
    return os.path.join(os.path.dirname(__file__), 'data/conversations.json')
# JSON veritabanını yükleme
def load_chat_database():
    try:
        with open(veritabanı_dosya_yolu(), 'r', encoding='utf-8') as f:
            return json.load(f), True
    except Exception as e:
        print(f"Veritabanı yüklenirken hata oluştu: {e}")
        return {"sorular": []}, False
chat_database, db_connected = load_chat_database()  # Veritabanını yükle







def get_response(message):
    try:
        try:
            message = message.lower()


            # Espri/Fıkra/Şaka kontrolü
            if "espri" in message:
                return get_joke("espri")
            elif "fıkra" in message:
                return get_joke("fıkra")
            elif any(word in message for word in ["şaka", "güldür", "komik"]):
                return get_joke("random")

            # Matematik işlemleri kontrolü
            elif any(op in message for op in ['+', '-', '*', '/', 'x']) or any(word in message for word in ['topla', 'çıkar', 'çarp', 'böl', 'kaç eder', 'sonucu nedir']):
                return solve_math_problem(message)

            # Film sorgusu
            elif "film" in message:
                film_query = message.replace("film", "").strip()
                return get_movie_info(film_query if film_query else None)

            # Kitap sorgusu
            elif "kitap" in message:
                book_query = message.replace("kitap", "").strip()
                return get_book_info(book_query if book_query else None)

            # Hava durumu sorgusu
            elif "hava durumu" in message:
                city = message.split("hava durumu")[-1].strip()
                if city:
                    return get_weather(city)
                return "Lütfen bir şehir belirtin."

            # Döviz kuru kontrolü
            currency_keywords = [
                'kur', 'döviz', 'usd', 'eur', 'gbp', 'jpy', 'chf', 'cny', 'sar', 'kwd', 'rub', 'pln',
                'sek', 'mxn', 'zar', 'brl', 'inr', 'aed', 'aud', 'cad', 'dkk', 'nok', 'try', 'krw',
                'kzt', 'azn', 'bgn', 'hrk', 'huf', 'dolar', 'euro', 'sterlin', 'yen', 'frank', 'yuan',
                'riyal', 'dinar', 'ruble', 'zloti', 'kron', 'peso', 'rand', 'real', 'rupi', 'dirhem',
                'won', 'tenge', 'manat', 'leva', 'kuna', 'forint'
            ]
            
            if any(word in message for word in currency_keywords):
                if 'amerikan doları' in message or 'abd doları' in message:
                    return get_currency_rate('USD')
                elif 'avustralya doları' in message:
                    return get_currency_rate('AUD')
                elif 'kanada doları' in message:
                    return get_currency_rate('CAD')
                elif 'dolar' in message:
                    return get_currency_rate('USD')
                
                currency_map = {
                    'euro': 'EUR',
                    'sterlin': 'GBP',
                    'yen': 'JPY',
                    'frank': 'CHF',
                    'yuan': 'CNY',
                    'riyal': 'SAR',
                    'dinar': 'KWD',
                    'ruble': 'RUB',
                    'zloti': 'PLN',
                    'kron': 'SEK',
                    'peso': 'MXN',
                    'rand': 'ZAR',
                    'real': 'BRL',
                    'rupi': 'INR',
                    'dirhem': 'AED',
                    'won': 'KRW',
                    'tenge': 'KZT',
                    'manat': 'AZN',
                    'leva': 'BGN',
                    'kuna': 'HRK',
                    'forint': 'HUF'
                }
                
                for keyword, currency_code in currency_map.items():
                    if keyword in message:
                        return get_currency_rate(currency_code)

            # Veritabanı kontrolü
            conversations = load_from_json()
            questions = [conv['soru'].lower() for conv in conversations]
            closest_match = get_close_matches(message, questions, n=1, cutoff=0.5)
            if closest_match:
                for conv in conversations:
                    if conv['soru'].lower() == closest_match[0]:
                        return conv['cevap']
            
            # GitHub araması
            programming_keywords = [
                "python", "c#", "c++", "c", "javascript", "typescript", "php", "html", "css", "sql",
                "mysql", "postgresql", "mongodb", "node.js", "express", "react", "angular", "vue.js",
                "laravel", "symfony", "django", "flask", "spring", "kotlin", "swift", "dart", "rust",
                "go", "ruby", "rails"
            ]
            
            if any(keyword in message for keyword in programming_keywords):
                query = message.replace("github", "").strip()
                return search_github_for_code(query)
            
            # Son çare olarak Wikipedia'da ara
            response = search_wikipedia(message)
            if not response or "bulunamadı" in response.lower():
                response = search_google(message)
            save_to_json(message, response)
            return response
        
        except Exception as e:
            print(f"Ön işleme hatası: {e}")  
    except Exception as e:
        return f"Mesaj işlenirken bir hata oluştu: {e}"






















def get_weather(city):
    api_key = '69e65273e8b45c821de13b7771395576'
    try:
        response = requests.get(f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=tr")
        if response.status_code == 200:
            weather_data = response.json()
            description = weather_data['weather'][0]['description']
            temperature = weather_data['main']['temp']
            return f"{city} için hava durumu: {description}, sıcaklık: {temperature}°C"
        else:
            return "Hava durumu bilgisi alınamadı."
    except Exception as e:
        return f"Hata: {e}"

def get_movie_info(query=None):
    """Film bilgisi ve önerileri getirir
    
    Args:
        query (str): Film sorgusu (tür veya isim)
    
    Returns:
        str: Film bilgileri
    """
    try:
        api_key = "94a8cbf09da92970cd13ff809fbf8fb6"  # TMDB API anahtarı
        
        # Film türlerine göre ID eşleştirmeleri
        genre_map = {
            "aksiyon": 28,
            "dram": 18,
            "komedi": 35,
            "korku": 27,
            "romantik": 10749,
            "bilim kurgu": 878
        }
        
        # Sorgu türüne göre URL oluştur
        if query and any(word in query.lower() for word in genre_map.keys()):
            genre_id = next((id for genre, id in genre_map.items() if genre in query.lower()), None)
            url = f"https://api.themoviedb.org/3/discover/movie?api_key={api_key}&language=tr-TR&sort_by=popularity.desc&with_genres={genre_id}&page={random.randint(1, 5)}"
        elif query:
            url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&language=tr-TR&query={query}"
        else:
            url = f"https://api.themoviedb.org/3/movie/popular?api_key={api_key}&language=tr-TR"
        
        # API'den film bilgilerini al
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            movies = data.get('results', [])
            
            if not movies:
                return "Film bulunamadı. Aksiyon, drama, komedi, korku, romantik veya bilim kurgu türlerini deneyebilirsiniz."
            
            # En fazla 3 film seç
            if len(movies) > 3:
                movies = random.sample(movies, 3)
            
            # Her film için detaylı bilgi al
            result = []
            for movie in movies:
                detail_url = f"https://api.themoviedb.org/3/movie/{movie['id']}?api_key={api_key}&language=tr-TR"
                detail_response = requests.get(detail_url)
                if detail_response.status_code == 200:
                    detail = detail_response.json()
                    movie_info = [
                        f"Film: {detail.get('title')} ({detail.get('release_date', '')[:4]})",
                        f"Tür: {', '.join(genre['name'] for genre in detail.get('genres', []))}",
                        f"IMDB: {detail.get('vote_average', 'N/A')}/10",
                        f"Süre: {detail.get('runtime', 'N/A')} dakika"
                    ]
                    result.append("\n".join(movie_info))
            
            return "\n\n".join(result)
        
        return "Film bilgisi alınamadı."
    except Exception as e:
        return f"Film bilgisi alınırken hata oluştu: {e}"

def get_book_info(query=None):
    """Kitap bilgisi ve önerileri getirir
    
    Args:
        query (str): Kitap sorgusu (tür veya isim)
    
    Returns:
        str: Kitap bilgileri
    """
    api_key = 'AIzaSyCLz-sPoqph_I9Z0MfKh7_xEx9rsosdu-c'  # Google Books API anahtarı
    try:
        # Kitap kategorileri
        categories = {
            "roman": "roman",
            "bilim kurgu": "science fiction",
            "fantastik": "fantasy",
            "polisiye": "detective",
            "macera": "adventure",
            "tarih": "history",
            "biyografi": "biography",
            "şiir": "poetry",
            "psikoloji": "psychology",
            "felsefe": "philosophy"
        }
        
        # Sorgu varsa kategoriye göre veya normal arama yap
        if query:
            category = next((cat_en for cat_tr, cat_en in categories.items() if cat_tr in query.lower()), None)
            if category:
                search_url = f"https://www.googleapis.com/books/v1/volumes?q=subject:{category}&langRestrict=tr&maxResults=5&orderBy=relevance&key={api_key}"
            else:
                search_url = f"https://www.googleapis.com/books/v1/volumes?q={query}&langRestrict=tr&maxResults=5&orderBy=relevance&key={api_key}"
        else:
            # Rastgele bir kategoriden kitap öner
            category = random.choice(list(categories.values()))
            search_url = f"https://www.googleapis.com/books/v1/volumes?q=subject:{category}&langRestrict=tr&maxResults=5&orderBy=relevance&key={api_key}"
        
        # API'den kitap bilgilerini al
        response = requests.get(search_url)
        if response.status_code == 200:
            books_data = response.json()
            if books_data.get('items'):
                books = random.sample(books_data['items'], min(3, len(books_data['items'])))
                book_details = []
                for book in books:
                    info = book['volumeInfo']
                    details = []
                    if info.get('title'): details.append(f"Kitap: {info['title']}")
                    if info.get('authors'): details.append(f"Yazar: {', '.join(info['authors'])}")
                    if info.get('publishedDate'): details.append(f"Yayın Tarihi: {info['publishedDate'][:4]}")
                    if info.get('pageCount'): details.append(f"Sayfa Sayısı: {info['pageCount']}")
                    if info.get('categories'): details.append(f"Kategori: {', '.join(info['categories'])}")
                    if info.get('averageRating'): details.append(f"Puan: {info['averageRating']}/5")
                    book_details.append("\n".join(details))
                
                return "\n\n".join(book_details)
                
        return "Kitap bulunamadı. Roman, bilim kurgu, fantastik, polisiye, macera, tarih, biyografi, şiir, psikoloji veya felsefe kategorilerini deneyebilirsiniz."
    except Exception as e:
        return f"Kitap bilgisi alınırken hata oluştu: {e}"

def get_joke(joke_type="random"):
    try:
        # JSON dosyasından fıkra ve esprileri yükle
        with open('data/jokes.json', 'r', encoding='utf-8') as file:
            jokes_data = json.load(file)
            
        if joke_type == "espri":
            # Sadece espri seç
            return f"Espri:\n{random.choice(jokes_data['espriler'])}"
        elif joke_type == "fıkra":
            # Sadece fıkra seç
            joke = random.choice(jokes_data['fıkralar'])
            return f"Fıkra:\n{joke['setup']}\n- {joke['punchline']}"
        else:
            # Rastgele seçim yap
            if random.choice([True, False]):
                joke = random.choice(jokes_data['fıkralar'])
                return f"Fıkra:\n{joke['setup']}\n- {joke['punchline']}"
            else:
                return f"Espri:\n{random.choice(jokes_data['espriler'])}"
    except Exception as e:
        return f"Üzgünüm, şu anda fıkra veya espri anlatamıyorum: {e}"

def solve_math_problem(problem):
    try:
        # Doğrudan matematik işlemlerini kontrol et
        if any(op in problem for op in ['+', '-', '*', '/', 'x']):
            # Güvenli bir şekilde işlemi değerlendir
            problem = problem.replace('x', '*')  # 'x' işaretini '*' ile değiştir
            # Sadece sayılar ve operatörleri al
            cleaned_problem = ''.join(c for c in problem if c.isdigit() or c in '+-*/')
            result = eval(cleaned_problem)
            return f"Sonuç: {result}"
            
        # Metin tabanlı matematik işlemlerini çöz
        if any(op in problem.lower() for op in ['topla', 'çıkar', 'çarp', 'böl', 'kaç eder', 'sonucu nedir']):
            numbers = [int(s) for s in problem.split() if s.isdigit()]
            if 'topla' in problem.lower() or 'kaç eder' in problem.lower():
                return f"Sonuç: {sum(numbers)}"
            elif 'çıkar' in problem.lower():
                if len(numbers) >= 2:
                    return f"Sonuç: {numbers[0] - numbers[1]}"
            elif 'çarp' in problem.lower():
                result = 1
                for num in numbers:
                    result *= num
                return f"Sonuç: {result}"
            elif 'böl' in problem.lower():
                if len(numbers) >= 2 and numbers[1] != 0:
                    return f"Sonuç: {numbers[0] / numbers[1]}"
        
        return search_google(problem)
    except Exception as e:
        return f"Problem çözülürken bir hata oluştu: {e}"

# JSON dosyasından verileri okuma fonksiyonu
def load_from_json():
    try:
        with open('data/conversations.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
            if not isinstance(data, list):
                print("Veritabanı formatı hatalı, boş liste oluşturuluyor.")
                return []
            return data
    except FileNotFoundError:
        print("Veritabanı dosyası bulunamadı, yeni dosya oluşturuluyor.")
        with open('data/conversations.json', 'w', encoding='utf-8') as file:
            json.dump([], file, ensure_ascii=False, indent=4)
        return []
    except json.JSONDecodeError:
        print("Veritabanı dosyası bozuk, boş liste oluşturuluyor.")
        return []
    except Exception as e:
        print(f"Veritabanı yüklenirken hata: {e}")
        return []



def search_google(query):
    try:
        # Google arama URL'si
        search_url = f"https://www.google.com/search?q={requests.utils.quote(query)}&hl=tr"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Önce featured snippet'i kontrol et
        featured_snippet = soup.find('div', {'class': 'IZ6rdc'})
        if featured_snippet:
            return featured_snippet.get_text().strip()
        
        # Normal arama sonuçlarını kontrol et
        search_results = soup.find_all('div', {'class': 'BNeawe s3v9rd AP7Wnd'})
        if search_results:
            # İlk sonucu al
            return search_results[0].get_text().strip()
        
        return None
        
    except Exception as e:
        print(f"Google araması sırasında hata: {e}")
        return None


@app.route('/get_response', methods=['POST'])
def process_message_route():
    try:
        message = request.json.get('message', '')
        if not message:
            return jsonify({'response': 'Mesaj boş olamaz'})
        
        response = get_response(message)
        return jsonify({'response': response})
        
    except Exception as e:
        print(f"İstek işlenirken hata: {e}")
        return jsonify({'response': 'Üzgünüm, bir hata oluştu.'})

# Kullanıcı kaydı
@app.route('/register', methods=['POST'])
def register():
    username = request.json.get('username')
    password = request.json.get('password')
    if not username or not password:
        return jsonify({'success': False, 'message': 'Kullanıcı adı ve şifre gereklidir.'})

    # Şifreyi ikiye böl
    half = len(password) // 2
    password_part1 = password[:half]
    password_part2 = password[half:]

    # Kullanıcıyı ve şifre parçalarını kaydet
    try:
        with open('data/users.json', 'r+', encoding='utf-8') as file:
            try:
                users = json.load(file)
                if not isinstance(users, dict):
                    users = {}  # Eğer dosya bir sözlük değilse, yeni bir sözlük oluştur
            except json.JSONDecodeError:
                users = {}  # JSON dosyası bozuksa, yeni bir sözlük oluştur

            if username in users:
                return jsonify({'success': False, 'message': 'Kullanıcı adı zaten mevcut.'})
            users[username] = True
            file.seek(0)
            json.dump(users, file, indent=4, ensure_ascii=False)

        with open('data/passwords.json', 'r+', encoding='utf-8') as file:
            try:
                passwords = json.load(file)
                if not isinstance(passwords, dict):
                    passwords = {}  # Eğer dosya bir sözlük değilse, yeni bir sözlük oluştur
            except json.JSONDecodeError:
                passwords = {}  # JSON dosyası bozuksa, yeni bir sözlük oluştur

            passwords[username] = {'part1': password_part1, 'part2': password_part2}
            file.seek(0)
            json.dump(passwords, file, indent=4, ensure_ascii=False)

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Kullanıcı girişi
@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    if not username or not password:
        return jsonify({'success': False, 'message': 'Kullanıcı adı ve şifre gereklidir.'})

    try:
        with open('data/passwords.json', 'r', encoding='utf-8') as file:
            passwords = json.load(file)
            if username not in passwords:
                return jsonify({'success': False, 'message': 'Kullanıcı bulunamadı.'})
            stored_password = passwords[username]
            if stored_password['part1'] + stored_password['part2'] == password:
                session['username'] = username
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'message': 'Şifre yanlış.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Ana sayfa
@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('login_page'))
    return render_template('index.html')

# Giriş sayfası
@app.route('/login')
def login_page():
    return render_template('login.html')

# Kayıt sayfası
@app.route('/register')
def register_page():
    return render_template('register.html')

# Metin tabanlı sohbet endpoint'i
@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '')
    
    
    
   

# Sesli komut endpoint'i


def search_github_for_code(query):
    """Belirtilen sorguya göre GitHub'da kod arar
    
    Args:
        query (str): Aranacak sorgu
    
    Returns:
        str: Bulunan en iyi projeler
    """
    try:
        # Programlama dili anahtar kelimeleri
        programming_languages = {
            'python': ['python', '.py'],
            'javascript': ['javascript', 'js', '.js'],
            'java': ['java', '.java'],
            'c++': ['cpp', 'c++', '.cpp'],
            'c#': ['c#', 'csharp', '.cs'],
            'php': ['php', '.php'],
            'ruby': ['ruby', '.rb'],
            'swift': ['swift', '.swift'],
            'go': ['golang', '.go'],
            'rust': ['rust', '.rs']
        }
        
        # Sorguyu analiz et
        query_lower = query.lower()
        selected_language = None
        
        # Programlama dilini belirle
        for lang, keywords in programming_languages.items():
            if any(keyword in query_lower for keyword in keywords):
                selected_language = lang
                break
        
        if not selected_language:
            return "Lütfen bir programlama dili belirtin."
            
        # Arama sorgusunu oluştur
        search_query = f"{query_lower} language:{selected_language}"
        
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Mozilla/5.0"
        }
        
        # GitHub API'sini kullanarak repo ara
        response = requests.get(
            f"https://api.github.com/search/repositories?q={search_query}&sort=stars&order=desc",
            headers=headers
        )
        
        if response.status_code == 200:
            results = response.json().get('items', [])
            if results:
                # En iyi 3 repoyu seç
                top_repos = []
                for repo in results[:3]:
                    repo_info = {
                        'name': repo['full_name'],
                        'description': repo['description'] or 'Açıklama yok',
                        'url': repo['html_url'],
                        'stars': repo['stargazers_count'],
                        'language': repo['language']
                    }
                    top_repos.append(
                        f"📦 {repo_info['name']}\n"
                        f"📝 {repo_info['description']}\n"
                        f"⭐ Yıldız: {repo_info['stars']}\n"
                        f"🔗 {repo_info['url']}\n"
                    )
                
                return "\n".join(top_repos)
            else:
                return f"{selected_language} ile ilgili repo bulunamadı."
        else:
            return "GitHub API'sine erişim sırasında bir hata oluştu."
            
    except Exception as e:
        return f"Arama yapılırken bir hata oluştu: {e}"

def search_wikipedia(query):
    try:
        # Türkçe karakterleri ve boşlukları URL için uygun hale getir
        encoded_query = requests.utils.quote(query)
        # Önce Wikipedia'da arama yap
        search_url = f"https://tr.wikipedia.org/w/api.php?action=query&list=search&srsearch={encoded_query}&format=json&utf8=1"
        search_response = requests.get(search_url)
        
        if search_response.status_code == 200:
            search_data = search_response.json()
            if search_data['query']['search']:
                # İlk sonucun başlığını al
                title = search_data['query']['search'][0]['title']
                # Başlığı kullanarak sayfa içeriğini al
                content_url = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(title)}"
                content_response = requests.get(content_url)
                
                if content_response.status_code == 200:
                    content_data = content_response.json()
                    wiki_result = content_data.get('extract')
                    if wiki_result:
                        return wiki_result
        
        # Wikipedia'da bilgi bulunamazsa Google'da ara
        return search_google(query)
    except Exception as e:
        # Hata durumunda da Google'da ara
        return search_google(query)

# Admin giriş sayfası
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'admin123':
            session['admin'] = True
            return redirect(url_for('admin_panel'))
        else:
            return render_template('admin/admin_login.html', error='Hatalı kullanıcı adı veya şifre!')
    return render_template('admin/admin_login.html')

# Admin paneli
@app.route('/admin')
def admin_panel():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    return render_template('admin/content.html')

# Kullanıcıları listeleme
@app.route('/get_users')
def get_users():
    try:
        with open('data/users.json', 'r', encoding='utf-8') as users_file, open('data/passwords.json', 'r', encoding='utf-8') as passwords_file:
            users = json.load(users_file)
            passwords = json.load(passwords_file)
        return jsonify({'users': [{'username': u, 'password': passwords[u]['part1'] + passwords[u]['part2']} for u in users]}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Kullanıcı ekleme
@app.route('/add_user', methods=['POST'])
def add_user():
    username = request.json.get('username')
    password = request.json.get('password')
    role = request.json.get('role')
    if not username or not password or not role:
        return jsonify({'success': False, 'message': 'Kullanıcı adı, şifre ve rol gereklidir.'})

    if role == 'admin':
        username_part1 = username[:len(username)//2]
        username_part2 = username[len(username)//2:]
        password_part1 = password[:len(password)//3]
        password_part2 = password[len(password)//3:2*len(password)//3]
        password_part3 = password[2*len(password)//3:]
        try:
            with open('data/admins.json', 'r+', encoding='utf-8') as file:
                try:
                    admins = json.load(file)
                    if not isinstance(admins, dict):
                        admins = {}
                except json.JSONDecodeError:
                    admins = {}
                if username in admins:
                    return jsonify({'success': False, 'message': 'Admin kullanıcı adı zaten mevcut.'})
                admins[username] = {
                    'username_part1': username_part1,
                    'username_part2': username_part2,
                    'password_part1': password_part1,
                    'password_part2': password_part2,
                    'password_part3': password_part3
                }
                file.seek(0)
                file.truncate()
                json.dump(admins, file, indent=4, ensure_ascii=False)
            return jsonify({'success': True})
        except FileNotFoundError:
            with open('data/admins.json', 'w', encoding='utf-8') as file:
                admins = {
                    username: {
                        'username_part1': username_part1,
                        'username_part2': username_part2,
                        'password_part1': password_part1,
                        'password_part2': password_part2,
                        'password_part3': password_part3
                    }
                }
                json.dump(admins, file, indent=4, ensure_ascii=False)
            return jsonify({'success': True})
    else:
        half = len(password) // 2
        password_part1 = password[:half]
        password_part2 = password[half:]
        try:
            with open('data/users.json', 'r+', encoding='utf-8') as file:
                users = json.load(file)
                if username in users:
                    return jsonify({'success': False, 'message': 'Kullanıcı adı zaten mevcut.'})
                users[username] = {'part1': password_part1, 'part2': password_part2}
                file.seek(0)
                json.dump(users, file, indent=4, ensure_ascii=False)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})

# Kullanıcı silme
@app.route('/delete_user', methods=['POST'])
def delete_user():
    username = request.json.get('username')
    try:
        with open('data/users.json', 'r+', encoding='utf-8') as file:
            users = json.load(file)
            if username in users:
                del users[username]
                file.seek(0)
                file.truncate()
                json.dump(users, file, indent=4, ensure_ascii=False)
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'message': 'Kullanıcı bulunamadı.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Anasayfa
@app.route('/admin/home')
def admin_home():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    return render_template('admin/home.html')

# Kullanıcılar
@app.route('/admin/users')
def admin_users():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    return render_template('admin/users.html')

# Yeni Üye Ekle
@app.route('/admin/add-user')
def admin_add_user():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    return render_template('admin/add_user.html')

# Gelir Giderler
@app.route('/admin/finance')
def admin_finance():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    return render_template('admin/finance.html')

# Reklamlar
@app.route('/admin/ads')
def admin_ads():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    return render_template('admin/ads.html')

# Kullanıcı şifresini güncelle
@app.route('/update_user', methods=['POST'])
def update_user():
    username = request.json.get('username')
    new_password = request.json.get('password')
    if not username or not new_password:
        return jsonify({'success': False, 'message': 'Kullanıcı adı ve yeni şifre gereklidir.'})

    half = len(new_password) // 2
    password_part1 = new_password[:half]
    password_part2 = new_password[half:]

    try:
        with open('data/passwords.json', 'r+', encoding='utf-8') as file:
            passwords = json.load(file)
            if username in passwords:
                passwords[username] = {'part1': password_part1, 'part2': password_part2}
                file.seek(0)
                file.truncate()
                json.dump(passwords, file, indent=4, ensure_ascii=False)
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'message': 'Kullanıcı bulunamadı.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def save_to_json(user_message, bot_response):
    data = {
        "soru": user_message,
        "cevap": bot_response
    }
    try:
        with open('data/conversations.json', 'r+', encoding='utf-8') as file:
            try:
                # Mevcut veriyi yükle
                file_data = json.load(file)
                if not isinstance(file_data, list):
                    file_data = []  # Dosya bir liste değilse, boş liste oluştur
            except json.JSONDecodeError:
                file_data = []  # JSON dosyası bozuksa, boş liste oluştur

            # Aynı veri zaten varsa kaydetme
            if not any(conv['soru'].lower() == user_message.lower() and conv['cevap'].lower() == bot_response.lower() for conv in file_data):
                file_data.append(data)
                file.seek(0)
                json.dump(file_data, file, indent=4, ensure_ascii=False)
    except FileNotFoundError:
        # Dosya yoksa yeni bir dosya oluştur ve veri kaydet
        with open('data/conversations.json', 'w', encoding='utf-8') as file:
            json.dump([data], file, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving to JSON: {e}")

def get_currency_rate(currency):
    try:
        # Para birimi kısaltmaları ve karşılıkları
        currency_dict = {
            'ABD DOLARI': 'USD',
            'AMERIKAN DOLARI': 'USD',
            'DOLAR': 'USD',
            'USD': 'USD',
            'EURO': 'EUR',
            'EUR': 'EUR',
            'STERLIN': 'GBP',
            'GBP': 'GBP',
            'YEN': 'JPY',
            'JAPON YENI': 'JPY',
            'ISVICRE FRANGI': 'CHF',
            'FRANK': 'CHF',
            'YUAN': 'CNY',
            'RIYAL': 'SAR',
            'DINAR': 'KWD',
            'RUBLE': 'RUB',
            'ZLOTI': 'PLN',
            'ISVEC KRONU': 'SEK',
            'PESO': 'MXN',
            'RAND': 'ZAR',
            'REAL': 'BRL',
            'RUPI': 'INR',
            'DIRHEM': 'AED',
            'AVUSTRALYA DOLARI': 'AUD',
            'AUD': 'AUD',
            'KANADA DOLARI': 'CAD',
            'CAD': 'CAD',
            'DANIMARKA KRONU': 'DKK',
            'NORVEC KRONU': 'NOK',
            'TURK LIRASI': 'TRY',
            'TL': 'TRY',
            'GUNEY KORE WONU': 'KRW',
            'WON': 'KRW',
            'TENGE': 'KZT',
            'MANAT': 'AZN',
            'LEVA': 'BGN',
            'KUNA': 'HRK',
            'FORINT': 'HUF'
        }

        # Gelen para birimini büyük harfe çevir ve Türkçe karakterleri düzelt
        currency = currency.upper()
        currency = currency.replace('İ', 'I').replace('Ş', 'S').replace('Ğ', 'G').replace('Ü', 'U').replace('Ö', 'O').replace('Ç', 'C')
        
        # Eğer para birimi sözlükte varsa kısaltmasını al
        for key, value in currency_dict.items():
            if key in currency:
                currency = value
                break

        # TRY çevrimi ekle
        if not '/' in currency:
            currency = f"{currency}/TRY"
            
        url = f"https://www.google.com/search?q={currency}+kuru"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Kur bilgisini bul
        rate = soup.find('div', class_='BNeawe iBp4i AP7Wnd')
        if rate:
            return f"{currency} güncel kuru: {rate.text}"
        return f"Kur bilgisi bulunamadı: {currency}"
    except Exception as e:
        return f"Döviz kuru alınırken bir hata oluştu: {e}"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
